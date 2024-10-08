# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import copy
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Header

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.exceptions import Forbidden
from dataset.components.file.crud import FileCRUD
from dataset.components.file.dependencies import get_file_crud
from dataset.components.file.schemas import DatasetFileDelete
from dataset.components.file.schemas import DatasetFileMove
from dataset.components.file.schemas import DatasetFileRename
from dataset.components.file.schemas import ImportDataPost
from dataset.components.file.schemas import LegacyFileListResponse
from dataset.components.file.schemas import LegacyFileResponse
from dataset.components.file.tasks import FileOperationTasks
from dataset.components.folder.crud import FolderCRUD
from dataset.components.folder.dependencies import get_folder_crud
from dataset.dependencies.services import get_project_service
from dataset.logger import logger
from dataset.services import ProjectService

router = APIRouter(prefix='/dataset', tags=['Files'])


@router.put(
    '/{dataset_id}/files',
    summary='API will recieve the file list from a project and copy them under the dataset.',
    response_model=LegacyFileResponse,
)
async def import_dataset(
    dataset_id: UUID,
    request_payload: ImportDataPost,
    background_tasks: BackgroundTasks,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    file_taks: FileOperationTasks = Depends(),
    file_crud: FileCRUD = Depends(get_file_crud),
    project_service: ProjectService = Depends(get_project_service),
    Session_ID: Optional[str] = Header(None),
) -> LegacyFileResponse:
    """API imports file list from project to dataset."""
    logger.info('IMPORT FILES: begin endpoint')

    import_list = request_payload.source_list
    oper = request_payload.operator
    project_id = request_payload.project_geid

    dataset = await dataset_crud.retrieve_by_id(dataset_id)
    logger.info('IMPORT FILES: retrieve dataset.')
    if dataset.project_id and str(dataset.project_id) != project_id:
        raise Forbidden()
    project = await project_service.get_by_id(project_id)
    logger.info('IMPORT FILES: retrieve project.')
    import_list, wrong_file = await file_crud.validate_files_folders(import_list, project['code'], items_type='project')
    for file in import_list:
        file['parent'] = None
        file['parent_path'] = None
    logger.info('IMPORT FILES: files and folders validated.')

    duplicate, import_list = await file_crud.remove_duplicate_file(import_list, dataset.code)
    logger.info('IMPORT FILES: duplicated removed.')

    if len(import_list) > 0:
        background_tasks.add_task(
            file_taks.copy_files_worker,
            dataset_crud,
            import_list,
            dataset,
            oper,
            project_id,
            project['code'],
            Session_ID,
        )

    logger.info('IMPORT FILES: added copy_files_worker')
    return LegacyFileResponse(result={'processing': import_list, 'ignored': wrong_file + duplicate})


@router.delete(
    '/{dataset_id}/files', summary='API will delete file by geid from list', response_model=LegacyFileResponse
)
async def delete_files(
    dataset_id: UUID,
    request_payload: DatasetFileDelete,
    background_tasks: BackgroundTasks,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    file_taks: FileOperationTasks = Depends(),
    file_crud: FileCRUD = Depends(get_file_crud),
    Session_ID: Optional[str] = Header(None),
) -> LegacyFileResponse:
    """API deletes file by id within Dataset."""

    dataset_obj = await dataset_crud.retrieve_by_id(dataset_id)
    delete_list = request_payload.source_list
    delete_list, wrong_file = await file_crud.validate_files_folders(delete_list, dataset_obj.code)

    if len(delete_list) > 0:
        background_tasks.add_task(
            file_taks.delete_files_work,
            dataset_crud,
            delete_list,
            dataset_obj,
            request_payload.operator,
            Session_ID,
        )

    return LegacyFileResponse(result={'processing': delete_list, 'ignored': wrong_file})


@router.get(
    '/{dataset_id}/files', summary='API will list files under the target dataset', response_model=LegacyFileListResponse
)
async def list_files(
    dataset_id: UUID,
    folder_id: str = None,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    folder_crud: FolderCRUD = Depends(get_folder_crud),
) -> LegacyFileListResponse:
    """API list the children from folder_id within Dataser."""

    ret_routing = []
    dataset = await dataset_crud.retrieve_by_id(dataset_id)

    root_geid = folder_id if folder_id else None

    file_folder_nodes = await folder_crud.get_children(dataset.code, root_geid)

    if file_folder_nodes:
        parent_path = file_folder_nodes[0]['parent_path']
        ret_routing = parent_path.split('/') if parent_path else []

    total = len(file_folder_nodes)
    ret = {
        'data': file_folder_nodes,
        'route': ret_routing,
    }

    return LegacyFileListResponse(result=ret, total=total)


@router.post('/{dataset_id}/files', summary='API will move files within the dataset', response_model=LegacyFileResponse)
async def move_files(
    dataset_id: UUID,
    request_payload: DatasetFileMove,
    background_tasks: BackgroundTasks,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    file_taks: FileOperationTasks = Depends(),
    file_crud: FileCRUD = Depends(get_file_crud),
    Session_ID: Optional[str] = Header(None),
) -> LegacyFileResponse:
    """API moves files within the dataset."""
    dataset = await dataset_crud.retrieve_by_id(dataset_id)

    if request_payload.target_geid == str(dataset_id):
        target_folder = {
            'id': None,
            'name': None,
            'parent': None,
            'parent_path': None,
            'code': dataset.code,
        }
    else:
        target_folder = await file_crud.validate_files_target_folder(request_payload.target_geid, dataset.code)

    move_list = request_payload.source_list
    move_list, wrong_file = await file_crud.validate_files_folders(move_list, dataset.code)
    future_list = copy.deepcopy(move_list)
    for file in future_list:
        if request_payload.target_geid == dataset_id:
            file['parent'] = None
            file['parent_path'] = None
        else:
            file['parent'] = target_folder['id']
            file['parent_path'] = (target_folder['name'] if target_folder['name'] else '') + (
                '.' + file['parent_path'] if file['parent_path'] else ''
            )
    duplicate, future_list = await file_crud.remove_duplicate_file(future_list, dataset.code)
    final_list = []
    duplicated_ids = [item['id'] for item in duplicate]
    for item in move_list:
        if item['id'] not in duplicated_ids:
            final_list.append(item)

    if len(move_list) > 0:
        background_tasks.add_task(
            file_taks.move_file_worker,
            final_list,
            dataset,
            request_payload.operator,
            target_folder,
            Session_ID,
        )
    return LegacyFileResponse(result={'processing': final_list, 'ignored': wrong_file + duplicate})


@router.post(
    '/{dataset_id}/files/{target_file}',
    summary='API will update files within the dataset',
    response_model=LegacyFileResponse,
)
async def rename_file(
    dataset_id: UUID,
    target_file: str,
    request_payload: DatasetFileRename,
    background_tasks: BackgroundTasks,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    file_taks: FileOperationTasks = Depends(),
    file_crud: FileCRUD = Depends(get_file_crud),
    Session_ID: Optional[str] = Header(None),
) -> LegacyFileResponse:
    """API will rename file/folder within dataset."""

    new_name = request_payload.new_name
    duplicate = []

    dataset = await dataset_crud.retrieve_by_id(dataset_id)

    rename_list, wrong_file = await file_crud.validate_files_folders([target_file], dataset.code)
    if len(rename_list) > 0:
        future_list = copy.deepcopy(rename_list)
        future_list[0]['name'] = new_name

        duplicate, _ = await file_crud.remove_duplicate_file(future_list, dataset.code)

        if len(duplicate) > 0:
            duplicate = rename_list
            rename_list = []

    if len(rename_list) > 0:
        background_tasks.add_task(
            file_taks.rename_file_worker,
            rename_list[0],
            new_name,
            dataset,
            request_payload.operator,
            Session_ID,
        )

    return LegacyFileResponse(result={'processing': rename_list, 'ignored': wrong_file + duplicate})
