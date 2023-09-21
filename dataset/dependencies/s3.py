# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.object_storage.s3 import S3Client
from dataset.config import get_settings

settings = get_settings()


async def get_s3_client() -> S3Client:
    s3_endpoint = f'{settings.S3_HOST}:{settings.S3_PORT}'
    client = await S3Client.initialize(
        s3_endpoint, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY, settings.S3_HTTPS_ENABLED
    )
    return client
