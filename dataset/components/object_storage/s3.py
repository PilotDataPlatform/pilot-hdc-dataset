# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import BinaryIO

from common import get_boto3_admin_client
from common import get_boto3_client
from common.object_storage_adaptor.boto3_admin_client import Boto3AdminClient
from common.object_storage_adaptor.boto3_client import Boto3Client

from dataset.config import get_settings

settings = get_settings()


class BucketNotFound(Exception):
    """Raised when specified bucket is not found."""


class S3Client:
    """Class that combines two boto3 clients from common package for better usability."""

    boto_client: Boto3Client
    boto_admin_client: Boto3AdminClient

    @classmethod
    async def initialize(cls, endpoint: str, access_key: str, secret_key: str, https: bool = False) -> 'S3Client':
        """Create an instance of S3Client with initialized boto3 clients."""
        s3_client = cls()
        s3_client.boto_client = await get_boto3_client(
            endpoint=endpoint, access_key=access_key, secret_key=secret_key, https=https
        )
        s3_client.boto_admin_client = await get_boto3_admin_client(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
        )
        s3_client.boto_public_client = await get_boto3_client(
            endpoint=settings.S3_PUBLIC, access_key=access_key, secret_key=secret_key, https=settings.S3_PUBLIC_HTTPS
        )
        return s3_client

    async def create_bucket(self, bucket: str) -> dict[str, Any]:
        """Create a bucket in S3."""
        return await self.boto_admin_client.create_bucket(bucket)

    async def set_bucket_versioning(self, bucket: str) -> dict[str, Any]:
        """Set versioning for a bucket."""
        return await self.boto_admin_client.set_bucket_versioning(bucket)

    async def create_bucket_encryption(self, bucket: str) -> dict[str, Any]:
        """Create encryption for a bucket."""
        return await self.boto_admin_client.create_bucket_encryption(bucket)

    async def remove_bucket(self, bucket: str) -> dict[str, Any]:
        """Delete a bucket from S3."""
        return await self.boto_admin_client.delete_bucket(bucket)

    async def upload_file(self, bucket: str, key: str, f: BinaryIO) -> None:
        """Upload file to S3."""
        await self.boto_client.upload_object(bucket, key, f)

    async def download_file(self, bucket: str, key: str, local_path: str) -> None:
        """Download file from S3."""
        await self.boto_client.download_object(bucket, key, local_path)

    async def get_download_presigned_url(self, bucket: str, file_path: str) -> str:
        """Get generate a download presigned url."""
        return await self.boto_public_client.get_download_presigned_url(bucket, file_path)

    async def get_file_body(self, bucket: str, file_path: str, file_limit_size: int = settings.MAX_PREVIEW_SIZE) -> str:
        """Get file body with file size limit."""
        async with self.boto_client._session.client(
            's3', endpoint_url=self.boto_client.endpoint, config=self.boto_client._config
        ) as s3:
            res = await s3.get_object(Bucket=bucket, Key=file_path, Range=f'bytes=0-{file_limit_size}')
            content = await res['Body'].read()
            return content.decode()

    async def delete_object(self, bucket: str, file_path: str) -> None:
        await self.boto_client.delete_object(bucket, file_path)

    async def copy_object(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str) -> dict[str, Any]:
        return await self.boto_client.copy_object(source_bucket, source_key, dest_bucket, dest_key)
