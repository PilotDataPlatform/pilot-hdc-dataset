# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from aiokafka.errors import KafkaConnectionError
from sqlalchemy.exc import SQLAlchemyError


async def test_health_should_return_204_with_empty_response(client):
    response = await client.get('/v1/health')
    assert response.status_code == 204
    assert not response.text


async def test_health_should_return_503_when_db_fails(client, mocker):
    mocker.patch('sqlalchemy.ext.asyncio.engine.AsyncConnection.get_raw_connection', side_effect=SQLAlchemyError)

    response = await client.get('/v1/health')

    assert response.status_code == 503
    assert not response.text


async def test_health_should_return_503_when_kafka_fails(client, mocker):
    mocker.patch('dataset.dependencies.kafka.GetKafkaClient.__call__', side_effect=KafkaConnectionError)

    response = await client.get('/v1/health')

    assert response.status_code == 503
    assert not response.text
