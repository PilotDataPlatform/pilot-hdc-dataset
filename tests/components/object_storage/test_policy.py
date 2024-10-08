# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from common import NotFoundError

from dataset.components.object_storage.policy import get_policy_manager
from dataset.dependencies import get_s3_client


class TestPolicyManager:
    async def test_policy_manager_create_policiy_on_update_or_create_when_policy_does_not_exist(
        self, minio_container, minio_client
    ):
        code = 'test-code'
        username = 'any_1'
        s3_client = await get_s3_client()
        await s3_client.create_bucket(code)
        policy_manager = await get_policy_manager()
        await policy_manager.update_or_create_policies(code, username)
        policy = await minio_client.get_IAM_policy(username)
        resources_list = policy['Policy']['Statement'][0]['Resource']
        assert resources_list == [f'arn:aws:s3:::{code}/*']

    async def test_policy_manager_update_policiy_on_update_or_create_when_policy_exists(
        self, minio_container, minio_client
    ):
        code_1 = 'another-test-code1'
        code_2 = 'another-test-code2'
        username = 'any_2'
        s3_client = await get_s3_client()
        await s3_client.create_bucket(code_1)
        await s3_client.create_bucket(code_2)

        policy_manager = await get_policy_manager()
        await policy_manager.update_or_create_policies(code_1, username)
        await policy_manager.update_or_create_policies(code_2, username)

        policy = await minio_client.get_IAM_policy(username)
        resources_list = policy['Policy']['Statement'][0]['Resource']
        assert set(resources_list) == {f'arn:aws:s3:::{code_1}/*', f'arn:aws:s3:::{code_2}/*'}

    async def test_policy_manager_rolls_back_created_policies(self, minio_container, minio_client):
        code = 'another-test-code'
        username = 'any_3'
        s3_client = await get_s3_client()
        await s3_client.create_bucket(code)
        policy_manager = await get_policy_manager()
        await policy_manager.update_or_create_policies(code, username)

        # rolling back policies creation
        await policy_manager.rollback_policies(username)
        with pytest.raises(NotFoundError):
            await minio_client.get_IAM_policy(username)
