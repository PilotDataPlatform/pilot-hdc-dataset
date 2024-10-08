# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

from common import get_minio_policy_client
from common.object_storage_adaptor.minio_policy_client import MinioPolicyClient
from common.object_storage_adaptor.minio_policy_client import NotFoundError

from dataset.components.object_storage.policy_templates import get_policy_template
from dataset.config import get_settings

settings = get_settings()


class PolicyManager:
    """Manager for dataset policies."""

    def __init__(self, minio_policy_client: MinioPolicyClient):
        self.minio_policy_client = minio_policy_client
        self.templates = get_policy_template

    async def update_or_create_policies(self, dataset_code: str, dataset_creator: str):
        """Add MinIO policies for respective dataset buckets users."""
        new_resource = f'arn:aws:s3:::{dataset_code}/*'
        try:
            dataset_creator_policy = await self.minio_policy_client.get_IAM_policy(dataset_creator)
            resources_list = dataset_creator_policy['Policy']['Statement'][0]['Resource']
            if new_resource not in resources_list:
                resources_list.append(new_resource)
                await self.minio_policy_client.create_IAM_policy(
                    dataset_creator, json.dumps(dataset_creator_policy['Policy'])
                )
        except NotFoundError:
            policy_content = self.templates(dataset_code)
            await self.minio_policy_client.create_IAM_policy(dataset_creator, policy_content)

    async def rollback_policies(self, dataset_creator: str) -> None:
        """Remove MinIO policies for respective dataset buckets users."""
        await self.minio_policy_client.delete_IAM_policy(dataset_creator)


async def get_policy_manager() -> PolicyManager:
    s3_endpoint = settings.S3_HOST + ':' + str(settings.S3_PORT)
    minio_client = await get_minio_policy_client(
        s3_endpoint, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY, https=settings.S3_HTTPS_ENABLED
    )
    return PolicyManager(minio_client)
