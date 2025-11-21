# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from common import get_minio_policy_client
from common.object_storage_adaptor.minio_policy_client import MinioPolicyClient


@pytest.fixture
async def minio_client(settings) -> MinioPolicyClient:
    s3_endpoint = settings.S3_HOST + ':' + str(settings.S3_PORT)
    yield await get_minio_policy_client(
        s3_endpoint, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY, https=settings.S3_HTTPS_ENABLED
    )
