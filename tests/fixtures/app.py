# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import asyncio
from collections.abc import AsyncIterator
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient

from dataset.app import create_app
from dataset.config import Settings
from dataset.config import get_settings
from dataset.dependencies import get_db_session


@pytest.fixture(scope='session')
def project_root() -> Path:
    path = Path(__file__)

    while not (path / 'pyproject.toml').is_file():
        path = path.parent

    return path


@pytest.fixture(scope='session')
def get_service_image(project_root) -> Callable[[str], str]:
    with open(project_root / 'docker-compose.yaml') as file:
        services = yaml.safe_load(file)['services']

    def get_image(service_name: str) -> str:
        return services[service_name]['image']

    return get_image


@pytest.fixture(scope='session')
def settings(redis_url, kafka_url) -> Settings:
    settings = get_settings()
    settings.REDIS_HOST = redis_url[0]
    settings.REDIS_PORT = redis_url[1]
    settings.KAFKA_URL = kafka_url
    return settings


@pytest.fixture
def app(event_loop, settings, db_session) -> Iterator[FastAPI]:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: settings
    yield app


@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
    asyncio.set_event_loop_policy(None)


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url='https://dataset') as client:
        yield client
