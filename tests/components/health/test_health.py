# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from dataset.config import get_settings
from dataset.dependencies.db import db_engine
from dataset.dependencies.db import get_db_session
from dataset.dependencies.kafka import kafka_client

pytestmark = pytest.mark.asyncio


@pytest.fixture()
def kafka(monkeypatch, kafka_url):
    settings = get_settings()
    monkeypatch.setattr(settings, 'KAFKA_URL', kafka_url)


async def test_health_should_return_204_with_empty_response(client, kafka):
    response = await client.get('/v1/health')
    assert response.status_code == 204
    assert not response.text


async def test_health_should_return_503_when_db_fails(override_dependencies, client, monkeypatch):
    settings = get_settings()
    db_engine.instance = None

    with override_dependencies({get_db_session: db_engine}):
        with monkeypatch.context() as m:
            m.setattr(settings, 'OPS_DB_URI', 'fake')
            response = await client.get('/v1/health')
    assert response.status_code == 503
    assert not response.text


async def test_health_should_return_503_when_kafka_fails(client, monkeypatch):
    settings = get_settings()
    kafka_client.aioproducer = None

    with monkeypatch.context() as m:
        m.setattr(settings, 'KAFKA_URL', 'fake')
        response = await client.get('/v1/health')

    assert response.status_code == 503
    assert not response.text
