# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from dataset.dependencies.db import GetDBEngine


@pytest.fixture
def get_db_engine() -> GetDBEngine:
    yield GetDBEngine()


async def test_instance_has_uninitialized_instance_attribute_after_creation(get_db_engine):
    assert get_db_engine.instance is None


async def test_call_returns_an_instance_of_async_engine(get_db_engine):
    db_engine = await get_db_engine()
    assert db_engine is get_db_engine.instance
    assert isinstance(db_engine, AsyncEngine)
