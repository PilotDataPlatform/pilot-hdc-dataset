# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest_asyncio
from testcontainers.redis import RedisContainer


@pytest_asyncio.fixture(scope='session')
def redis_url():
    with RedisContainer(password='auth') as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port)
        yield host, port
