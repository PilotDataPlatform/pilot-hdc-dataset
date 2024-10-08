# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.folder.activity_log import FolderActivityLog
from dataset.components.folder.crud import FolderCRUD
from dataset.components.folder.dependencies import get_folder_crud
from dataset.components.folder.schemas import FolderCreateSchema
from dataset.components.folder.schemas import LegacyFolderResponseSchema

router = APIRouter(prefix='/dataset', tags=['Folder'])


@router.post(
    '/{dataset_id}/folder',
    response_model=LegacyFolderResponseSchema,
    summary='Create an empty folder',
)
async def create_folder(
    dataset_id: str,
    data: FolderCreateSchema,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    folder_crud: FolderCRUD = Depends(get_folder_crud),
    activity_log: FolderActivityLog = Depends(),
) -> LegacyFolderResponseSchema:
    """Create an empty folder."""
    dataset = await dataset_crud.retrieve_by_id(dataset_id)
    folder = await folder_crud.create_folder(data, dataset.code)
    await activity_log.send_create_folder_event(folder=folder, user=data.username)
    return LegacyFolderResponseSchema(result=folder)
