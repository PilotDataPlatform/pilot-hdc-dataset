# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import os
from collections.abc import AsyncIterator
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer


@contextmanager
def chdir(directory: Path) -> Iterator[None]:
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture(scope='session')
def db_uri(get_service_image, project_root) -> Iterator[str]:
    postgres_image = get_service_image('postgres')

    with PostgresContainer(postgres_image, dbname='dataset') as postgres:
        database_uri = postgres.get_connection_url()

        config = Config('migrations/alembic.ini')
        with chdir(project_root):
            config.set_main_option('database_uri', database_uri)
            upgrade(config, 'head')

        yield database_uri.replace('+psycopg2', '+asyncpg')


@pytest.fixture(scope='session')
def db_engine(db_uri) -> AsyncEngine:
    return create_async_engine(db_uri)


@pytest.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    session = AsyncSession(bind=db_engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
