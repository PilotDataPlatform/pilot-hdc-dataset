# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from urllib.parse import urlparse

import pytest_asyncio
from alembic.command import downgrade
from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.postgres import PostgresContainer


@pytest_asyncio.fixture(scope='session')
def db_postgres():
    with PostgresContainer('postgres:14.1', dbname='dataset') as postgres:
        db_uri = postgres.get_connection_url()
        yield db_uri.replace(f'{urlparse(db_uri).scheme}://', 'postgresql+asyncpg://', 1)


@pytest_asyncio.fixture()
async def create_db(db_postgres):
    engine = create_async_engine(db_postgres)
    config = Config('./migrations/alembic.ini')
    upgrade(config, 'head')
    yield engine
    downgrade(config, 'base')
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(create_db):
    try:
        session = AsyncSession(
            create_db,
            expire_on_commit=False,
        )
        yield session
        await session.commit()
    finally:
        await session.close()


@pytest_asyncio.fixture()
def test_db(db_session):
    yield db_session
