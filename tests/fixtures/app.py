# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import asyncio
from contextlib import AbstractContextManager
from typing import Any
from typing import Callable

import pytest
import pytest_asyncio
from async_asgi_testclient import TestClient
from fastapi import FastAPI

from dataset.app import create_app
from dataset.config import get_settings
from dataset.dependencies import get_db_session


class OverrideDependencies(AbstractContextManager):
    """Temporarily override application dependencies using context manager."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.stashed_dependencies = {}
        self.dependencies_to_override = {}

    def __call__(self, dependencies: dict[Callable[..., Any], Callable[..., Any]]) -> 'OverrideDependencies':
        self.dependencies_to_override = dependencies
        return self

    def __enter__(self) -> 'OverrideDependencies':
        self.stashed_dependencies = self.app.dependency_overrides.copy()
        self.app.dependency_overrides.update(self.dependencies_to_override)
        return self

    def __exit__(self, *args: Any) -> None:
        self.app.dependency_overrides.clear()
        self.app.dependency_overrides.update(self.stashed_dependencies)
        self.dependencies_to_override = {}
        return None


@pytest.fixture
def override_dependencies(app) -> OverrideDependencies:
    yield OverrideDependencies(app)


@pytest_asyncio.fixture(autouse=True)
def set_settings(monkeypatch, db_postgres, redis_url):
    settings = get_settings()
    monkeypatch.setattr(settings, 'REDIS_HOST', redis_url[0])
    monkeypatch.setattr(settings, 'REDIS_PORT', redis_url[1])
    monkeypatch.setattr(settings, 'OPS_DB_URI', db_postgres)


@pytest.fixture
def app(event_loop, db_session) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    yield app


@pytest_asyncio.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
    asyncio.set_event_loop_policy(None)


@pytest_asyncio.fixture
async def client(app):
    async with TestClient(app) as client:
        yield client
