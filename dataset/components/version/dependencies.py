# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends
from redis.asyncio import StrictRedis
from sqlalchemy.ext.asyncio import AsyncSession

from dataset.components.file.dependencies import get_locking_manager
from dataset.components.file.locks import LockingManager
from dataset.components.folder.crud import FolderCRUD
from dataset.components.folder.dependencies import get_folder_crud
from dataset.components.object_storage.s3 import S3Client
from dataset.components.version.activity_log import VersionActivityLog
from dataset.components.version.activity_log import get_version_activity_log
from dataset.components.version.crud import VersionCRUD
from dataset.components.version.publisher import VersionPublisher
from dataset.dependencies import get_db_session
from dataset.dependencies.redis import get_redis_client
from dataset.dependencies.s3 import get_s3_client
from dataset.dependencies.services import get_metadata_service
from dataset.services.metadata import MetadataService


def get_version_crud(db_session: AsyncSession = Depends(get_db_session)) -> VersionCRUD:
    """Return an instance of VersionCRUD as a dependency."""

    return VersionCRUD(db_session)


async def get_version_publisher(
    redis_client: StrictRedis = Depends(get_redis_client),
    version_crud: VersionCRUD = Depends(get_version_crud),
    locking_manager: LockingManager = Depends(get_locking_manager),
    folder_crud: FolderCRUD = Depends(get_folder_crud),
    metadata_service: MetadataService = Depends(get_metadata_service),
    s3_client: S3Client = Depends(get_s3_client),
    activity_log: VersionActivityLog = Depends(get_version_activity_log),
) -> VersionPublisher:
    """Return an instance of VersionPublisher as a dependency."""
    return VersionPublisher(
        redis_client, version_crud, locking_manager, folder_crud, metadata_service, s3_client, activity_log
    )
