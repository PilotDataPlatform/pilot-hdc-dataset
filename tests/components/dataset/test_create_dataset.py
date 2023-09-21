# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock
from uuid import UUID

import pytest

from dataset.components.dataset.activity_log import DatasetActivityLog
from dataset.components.dataset.schemas import DatasetResponseSchema

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('code', [('ot'), ('ascbdascbdascbdascbdascbdascbda12'), ('ps!@#'), (' ')])
async def test_create_dataset_invalid_code_should_return_400(client, code, jq, minio_container):
    payload = {
        'creator': 'amyguindoc14',
        'title': '123',
        'authors': ['123'],
        'type': 'GENERAL',
        'description': '123',
        'code': code,
    }
    res = await client.post('/v1/datasets/', json=payload)
    assert res.status_code == 422
    body = jq(res)
    error = body('.detail').first()
    assert error[0]['loc'] == ['body', 'code']
    assert error[0]['msg'] == 'string does not match regex "^[a-z0-9]{3,32}$"'


async def test_create_dataset_long_title_should_return_422(client, jq, faker, minio_container):
    payload = {
        'creator': 'amyguindoc14',
        'title': faker.text(1000),
        'authors': ['123'],
        'type': 'GENERAL',
        'description': '123',
        'code': 'anycode',
    }
    res = await client.post('/v1/datasets/', json=payload)
    assert res.status_code == 422
    body = jq(res)
    error = body('.detail').first()
    assert error[0]['loc'] == ['body', 'title']
    assert error[0]['msg'] == 'ensure this value has at most 100 characters'


@mock.patch.object(DatasetActivityLog, 'send_dataset_on_create_event')
async def test_create_dataset_should_return_200(
    mock_dataset_activity_log, client, dataset_crud, minio_container, minio_client, s3_test_client, jq
):
    payload = {
        'creator': 'amyguindoc14',
        'title': '123',
        'authors': ['123'],
        'type': 'GENERAL',
        'description': '123',
        'code': 'datasetcode',
        'tags': ['{!@#$%^&*()_{}:\\?><'],
        'modality': ['anatomical approach'],
    }
    response = await client.post('/v1/datasets/', json=payload)
    assert response.status_code == 200
    body = jq(response)
    received_dataset_id = body('.id').first()
    created_dataset = await dataset_crud.retrieve_by_id(UUID(received_dataset_id))
    assert response.json() == DatasetResponseSchema.from_orm(created_dataset).to_payload()
    assert await minio_client.get_IAM_policy(created_dataset.creator)
    assert s3_test_client.check_if_bucket_exists(created_dataset.code)
    await dataset_crud.delete(created_dataset.id)
    mock_dataset_activity_log.assert_called_with(created_dataset)


async def test_duplicated_dataset_code_should_return_409(client, dataset_factory, minio_container):
    dataset = await dataset_factory.create()
    payload = {
        'creator': 'amyguindoc14',
        'title': '123',
        'authors': ['123'],
        'type': 'GENERAL',
        'description': '123',
        'code': dataset.code,
    }
    res = await client.post('/v1/datasets/', json=payload)
    assert res.status_code == 409
    assert res.json() == {
        'error': {'code': 'dataset.already_exists', 'details': 'Dataset with this code already exists.'}
    }
