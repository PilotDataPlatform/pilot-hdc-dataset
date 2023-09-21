# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from fastapi import Depends

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.models import Dataset
from dataset.components.file.activity_log import FileActivityLogService
from dataset.components.file.crud import FileCRUD
from dataset.components.file.dependencies import get_file_crud
from dataset.components.file.dependencies import get_locking_manager
from dataset.components.file.locks import LockingManager
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.file.types import EActionType
from dataset.components.file.types import EFileStatus
from dataset.components.folder.crud import FolderCRUD
from dataset.components.folder.dependencies import get_folder_crud
from dataset.components.schemas import BaseSchema
from dataset.config import get_settings
from dataset.logger import logger
from dataset.services.task_stream import TaskStreamService

settings = get_settings()


class FileOperationTasks:
    """File operations that run in background tasks."""

    def __init__(
        self,
        file_crud: FileCRUD = Depends(get_file_crud),
        folder_crud: FolderCRUD = Depends(get_folder_crud),
        locking_manager: LockingManager = Depends(get_locking_manager),
        task_stream_service: TaskStreamService = Depends(),
        file_act_notifier: FileActivityLogService = Depends(),
    ):
        self.file_crud = file_crud
        self.folder_crud = folder_crud
        self.locking_manager = locking_manager
        self.task_stream_service = task_stream_service
        self.file_act_notifier = file_act_notifier

    async def recursive_copy(
        self,
        current_nodes: List[Dict[str, Any]],
        dataset: Dataset,
        oper: str,
        current_root_path: str,
        parent_node: Dict[str, Any],
        job_tracker: Dict[str, Any] = None,
        new_name: str = None,
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Recursively adds all children from a specific parent to a dataset."""

        num_of_files = 0
        total_file_size = 0
        new_lv1_nodes = []

        for ff_object in current_nodes:
            ff_geid = ff_object.get('id')

            if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                continue

            if job_tracker:
                job_id = job_tracker['job_id'].get(ff_geid)
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.RUNNING.name,
                    dataset.code,
                    job_id,
                )

            if ff_object.get('type').lower() == 'file':
                new_node = await self.file_crud.create(
                    dataset,
                    ff_object,
                    oper,
                    parent_node,
                    new_name,
                )
                num_of_files += 1
                total_file_size += ff_object.get('size', 0)
                new_lv1_nodes.append(new_node)

            elif ff_object.get('type').lower() == 'folder':
                folder_name = new_name if new_name else ff_object.get('name')
                new_node = await self.folder_crud.import_folder(
                    parent_node.get('id'), current_root_path, oper, folder_name, dataset.code
                )
                new_lv1_nodes.append(new_node)

                if new_name:
                    filename = new_name
                else:
                    filename = ff_object.get('name')

                if not current_root_path:
                    next_root_path = filename
                else:
                    next_root_path = current_root_path + '/' + filename
                children_nodes = await self.folder_crud.get_children(
                    ff_object['container_code'], ff_object.get('id', None), ff_object['container_type']
                )
                num_of_child_files, num_of_child_size, _ = await self.recursive_copy(
                    children_nodes, dataset, oper, next_root_path, new_node
                )

                num_of_files += num_of_child_files
                total_file_size += num_of_child_size

            if job_tracker:
                job_id = job_tracker['job_id'].get(ff_geid)
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.SUCCEED.name,
                    dataset.code,
                    job_id,
                )

        return num_of_files, total_file_size, new_lv1_nodes

    async def recursive_delete(
        self, current_nodes: List[Dict[str, Any]], dataset: Dataset, oper: str, job_tracker: Dict[str, Any] = None
    ) -> Tuple[int, int]:
        """Recursively deletes all children from a specific parent from a dataset."""

        num_of_files = 0
        total_file_size = 0
        for ff_object in current_nodes:
            ff_geid = ff_object.get('id')

            if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                continue

            if job_tracker:
                job_id = job_tracker['job_id'].get(ff_geid)
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.RUNNING.name,
                    dataset.code,
                    job_id,
                )

            if ff_object.get('type').lower() == 'file':
                await self.file_crud.delete(ff_object)

                num_of_files += 1
                total_file_size += ff_object.get('size', 0)
            elif ff_object.get('type').lower() == 'folder':
                children_nodes = await self.folder_crud.get_children(
                    ff_object.get('container_code'), ff_object.get('id')
                )
                logger.info('children to be deleted', extra={'children_nodes': children_nodes})
                num_of_child_files, num_of_child_size = await self.recursive_delete(children_nodes, dataset, oper)

                await self.file_crud.metadata_service.delete_object(ff_object.get('id'))

                num_of_files += num_of_child_files
                total_file_size += num_of_child_size

            if job_tracker:
                job_id = job_tracker['job_id'].get(ff_geid)
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.SUCCEED.name,
                    dataset.code,
                    job_id,
                )

        return num_of_files, total_file_size

    async def copy_files_worker(
        self,
        dataset_crud: DatasetCRUD,
        import_list: List[Dict[str, Any]],
        dataset: Dataset,
        oper: str,
        source_project_id: str,
        project_code: str,
        session_id: str,
    ) -> None:
        """Background task responsible to add list of files/folders from dataset."""

        action = EActionType.data_import.name
        job_tracker = await self.task_stream_service.initialize_file_jobs(session_id, action, import_list, dataset.code)

        try:
            locked_node, err = await self.locking_manager.recursive_lock_import(
                dataset.code, import_list, settings.DATASET_FILE_FOLDER
            )

            if err:
                raise err
            num_of_files, total_file_size, _ = await self.recursive_copy(
                import_list, dataset, oper, None, {}, job_tracker
            )

            logger.info(f'dataset {dataset.code} total_files increase')
            update_attribute = {
                'total_files': dataset.total_files + num_of_files,
                'size': dataset.size + total_file_size,
                'project_id': source_project_id,
            }
            await dataset_crud.update(dataset.id, BaseSchema(), **update_attribute)
            logger.info(f'dataset {dataset.code}: {num_of_files} files added, old total {dataset.total_files}')

            await self.file_act_notifier.send_on_import_event(dataset.code, project_code, import_list, oper)
        except Exception as e:
            logger.exception(f'{e}')
            for ff_object in import_list:
                job_id = job_tracker['job_id'].get(ff_object.get('id'))
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.FAILED.name,
                    dataset.code,
                    job_id,
                )
        finally:
            for resource_key, operation in locked_node:
                await self.locking_manager.unlock_resource(resource_key, operation)
        return

    async def move_file_worker(  # noqa: C901
        self,
        move_list: List[Dict[str, Any]],
        dataset: Dataset,
        oper: str,
        target_folder: Dict[str, Any],
        session_id: str,
    ) -> None:
        """Background task responsible to copy files/folders to new parents and remove from the old ones."""

        action = EActionType.data_transfer.name
        job_tracker = await self.task_stream_service.initialize_file_jobs(session_id, action, move_list, dataset.code)
        try:
            if not target_folder.get('id'):
                target_folder = {}
                target_folder_name = settings.DATASET_FILE_FOLDER
                target_parent_path = None
            else:
                target_folder_name = target_folder['name']
                target_parent_path = (
                    f'{target_folder["parent_path"]}/{target_folder["name"]}'
                    if target_folder['parent']
                    else target_folder['name']
                )

            locked_node, err = await self.locking_manager.recursive_lock_move_rename(move_list, target_folder_name)
            if err:
                raise err

            await self.recursive_copy(move_list, dataset, oper, target_parent_path, target_folder)
            await self.recursive_delete(move_list, dataset, oper, job_tracker=job_tracker)

            dff = settings.DATASET_FILE_FOLDER
            for ff_geid in move_list:
                if ff_geid.get('type').lower() == 'file':
                    minio_path = ff_geid.get('storage').get('location_uri').split('//')[-1]
                    _, _, old_path = tuple(minio_path.split('/', 2))
                    old_path = old_path.replace(dff, '', 1)
                else:
                    # update the relative path by remove `data` at begining
                    if target_folder.get('parent_path') and ff_geid.get('parent_path'):
                        old_path = ff_geid.get('parent_path')
                    else:
                        old_path = '/'

                if target_folder.get('parent_path'):
                    parent_path = target_folder.get('parent_path')
                    parent_path += '/' + target_folder_name
                else:
                    parent_path = target_folder_name
                if parent_path == 'data':
                    new_path = '/' + ff_geid.get('name')
                else:
                    new_path = '/' + parent_path + '/' + ff_geid.get('name')

                await self.file_act_notifier.send_on_move_event(dataset.code, ff_geid, oper, old_path, new_path)

        except Exception as e:
            logger.exception(f'{e}')
            for ff_object in move_list:
                job_id = job_tracker['job_id'].get(ff_object.get('id'))
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.FAILED.name,
                    dataset.code,
                    job_id,
                )
        finally:
            for resource_key, operation in locked_node:
                await self.locking_manager.unlock_resource(resource_key, operation)

        return

    async def delete_files_work(
        self, dataset_crud: DatasetCRUD, delete_list: List[Dict[str, Any]], dataset: Dataset, oper: str, session_id: str
    ) -> None:
        """Background task responsible to remove list of files/folders from dataset."""
        deleted_files = []
        action = EActionType.data_delete.name
        job_tracker = await self.task_stream_service.initialize_file_jobs(session_id, action, delete_list, dataset.code)
        try:
            locked_node, err = await self.locking_manager.recursive_lock_delete(delete_list)
            if err:
                raise err
            num_of_files, total_file_size = await self.recursive_delete(delete_list, dataset, oper, job_tracker)

            for ff_geid in delete_list:
                if ff_geid.get('type').lower() == 'file':
                    minio_path = ff_geid.get('storage').get('location_uri').split('//')[-1]
                    _, _, obj_path = tuple(minio_path.split('/', 2))

                    dff = settings.DATASET_FILE_FOLDER + '/'
                    obj_path = obj_path[: len(dff)].replace(dff, '') + obj_path[len(dff) :]
                    deleted_files.append(obj_path)

                else:
                    dff = settings.DATASET_FILE_FOLDER
                    temp = ff_geid.get('parent_path')
                    if not temp:
                        temp = settings.DATASET_FILE_FOLDER

                    frp = ''
                    if dff != temp:
                        dff = dff + '/'
                        frp = temp.replace(dff, '', 1)
                    deleted_files.append(frp + ff_geid.get('name'))

            logger.info(f'dataset {dataset.code} total_files decreased')
            total_files = dataset.total_files - num_of_files
            total_size = dataset.size - total_file_size
            update_attribute = {
                'total_files': total_files if total_files > 0 else 0,
                'size': total_size if total_size > 0 else 0,
            }
            await dataset_crud.update(dataset.id, BaseSchema(), **update_attribute)
            logger.info(f'dataset {dataset.code} : {num_of_files} files removed, old total {dataset.total_files}')
            await self.file_act_notifier.send_on_delete_event(dataset.code, delete_list, oper)

        except Exception as e:
            logger.exception(f'{e}')

            for ff_object in delete_list:
                job_id = job_tracker['job_id'].get(ff_object.get('id'))
                await self.task_stream_service.update_job_status(
                    job_tracker['session_id'],
                    ff_object,
                    job_tracker['action'],
                    EFileStatus.FAILED.name,
                    dataset.code,
                    job_id,
                )
        finally:
            for resource_key, operation in locked_node:
                await self.locking_manager.unlock_resource(resource_key, operation)

        return

    async def rename_file_worker(
        self, old_file: Dict[str, Any], new_name: str, dataset: Dataset, oper: str, session_id: str
    ) -> None:
        """Background task responsible to copy file/folder to with new name and remove the old one."""

        action = EActionType.data_rename.name
        job_tracker = await self.task_stream_service.initialize_file_jobs(session_id, action, [old_file], dataset.code)

        job_id = job_tracker['job_id'].get(old_file.get('id'))
        await self.task_stream_service.update_job_status(
            job_tracker['session_id'],
            old_file,
            job_tracker['action'],
            EFileStatus.RUNNING.name,
            dataset.code,
            job_id,
        )

        parent_id = old_file.get('parent')
        if parent_id:
            # if parent exists, get information about it from metadata service
            parent_node = await self.file_crud.metadata_service.get_by_id(parent_id)
        else:
            # if parent does not exist (file in root directory)
            parent_node = {}

        try:
            locked_node, err = await self.locking_manager.recursive_lock_move_rename(
                nodes=[old_file],
                root_path=old_file.get('parent_path') or 'data',  # root path can't be None
                new_name=new_name,
            )
            if err:
                raise err

            await self.recursive_copy(
                current_nodes=[old_file],
                dataset=dataset,
                oper=oper,
                current_root_path=old_file.get('parent_path'),  # current root path can be None for top level
                parent_node=parent_node,
                new_name=new_name,
            )
            await self.recursive_delete(current_nodes=[old_file], dataset=dataset, oper=oper)

            await self.task_stream_service.update_job_status(
                job_tracker['session_id'],
                old_file,
                job_tracker['action'],
                EFileStatus.SUCCEED.name,
                dataset.code,
                job_id,
            )
            await self.file_act_notifier.send_on_rename_event(dataset.code, [old_file], oper, new_name)

        except Exception as e:
            logger.exception(f'{e}')

            await self.task_stream_service.update_job_status(
                job_tracker['session_id'],
                old_file,
                job_tracker['action'],
                EFileStatus.FAILED.name,
                dataset.code,
                job_id,
            )
        finally:
            for resource_key, operation in locked_node:
                await self.locking_manager.unlock_resource(resource_key, operation)

        return
