# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from aioredis import Redis
from fastapi import Depends

from dataset.config import get_settings

settings = get_settings()


class GetRedisClient:
    def __init__(self):
        self.client = None

    async def __call__(self) -> Redis:
        """Return an instance of Redis class."""
        if not self.client:
            self.client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
            )

        return self.client


redis_client = GetRedisClient()


async def get_redis_client(redis_client: Redis = Depends(redis_client)) -> Redis:
    return redis_client
