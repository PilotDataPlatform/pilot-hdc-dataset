# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from dataset.components.file.crud import FileCRUD
from dataset.components.file.locks import LockingManager
from dataset.components.folder.crud import FolderCRUD
from dataset.components.folder.dependencies import get_folder_crud
from dataset.components.object_storage.s3 import S3Client
from dataset.dependencies.s3 import get_s3_client
from dataset.dependencies.services import get_metadata_service
from dataset.services.metadata import MetadataService


async def get_file_crud(
    s3_client: S3Client = Depends(get_s3_client), metadata_service: MetadataService = Depends(get_metadata_service)
) -> FileCRUD:
    """Return FileCRUD instance."""
    return FileCRUD(s3_client, metadata_service)


async def get_locking_manager(folder_crud: FolderCRUD = Depends(get_folder_crud)) -> LockingManager:
    """Return LockingManager instance."""
    return LockingManager(folder_crud)
