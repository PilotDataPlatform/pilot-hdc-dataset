# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.object_storage.s3 import BucketNotFound
from dataset.components.object_storage.s3 import S3Client
from dataset.config import get_settings
from dataset.logger import logger

settings = get_settings()


class ObjectStorageManager:
    def __init__(self, s3_client: S3Client) -> None:
        self.s3_client = s3_client

    async def create_bucket(self, bucket_name: str) -> None:
        """Create a bucket and set versioning for it."""
        logger.info(f'Creating bucket {bucket_name}')
        await self.s3_client.create_bucket(bucket_name)

        if settings.S3_GATEWAY_ENABLED is False:
            logger.info(f'S3 Gateway is disabled, add versioning for {bucket_name}')
            await self.s3_client.set_bucket_versioning(bucket_name)
        else:
            logger.warning(f'S3 Gateway is enabled, versioning for {bucket_name} will not be enabled by API')

        if settings.S3_BUCKET_ENCRYPTION_ENABLED:
            logger.info(f'Bucket encryption enabled, encrypting {bucket_name}')
            await self.s3_client.create_bucket_encryption(bucket_name)
        else:
            logger.warning(f'Bucket encryption is not enabled, not encrypting {bucket_name}')

    async def remove_bucket(self, bucket_name: str) -> None:
        """Remove a bucket."""
        logger.info(f'Removing bucket {bucket_name}')
        try:
            await self.s3_client.remove_bucket(bucket_name)
        except BucketNotFound:
            pass
