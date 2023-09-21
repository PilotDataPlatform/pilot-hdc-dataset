# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.object_storage_manager import ObjectStorageManager
from dataset.components.object_storage.s3 import S3Client
from dataset.dependencies import get_db_session
from dataset.dependencies.s3 import get_s3_client


def get_dataset_crud(db_session: AsyncSession = Depends(get_db_session)) -> DatasetCRUD:
    """Return an instance of DatasetCRUD as a dependency."""

    return DatasetCRUD(db_session)


def get_object_storage_manager(s3_client: S3Client = Depends(get_s3_client)) -> ObjectStorageManager:
    """Returns an instance of ObjectStorageManager as a dependency."""
    return ObjectStorageManager(s3_client)
