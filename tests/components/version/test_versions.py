# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock
from uuid import uuid4

import pytest
from sqlalchemy import select

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.version.activity_log import VersionActivityLog
from dataset.components.version.models import Version
from dataset.components.version.schemas import VersionResponseSchema
from dataset.dependencies import get_s3_client

pytestmark = pytest.mark.asyncio


@mock.patch.object(VersionActivityLog, 'send_publish_version_succeed')
async def test_publish_version_should_start_background_task_and_return_200(
    mock_activity_log, client, minio_container, httpx_mock, dataset_factory, db_session, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    file_geid = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-1648138467'
    s3_client = await get_s3_client()
    await s3_client.create_bucket(dataset.code)
    await s3_client.boto_client.upload_object(dataset.code, 'obj/path', '')

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}'
            '&container_type=dataset&page_size=100&page=0'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': file_geid,
                    'parent': None,
                    'type': 'file',
                    'parent_path': 'obj/path',
                    'status': ItemStatusSchema.ACTIVE.name,
                    'storage': {'location_uri': f'http://anything.com/{dataset.code}/obj/path'},
                }
            ],
        },
    )

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}'
            '&container_type=dataset&page_size=100&page=0&type=file'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': file_geid,
                    'parent': None,
                    'type': 'file',
                    'parent_path': 'obj/path',
                    'status': ItemStatusSchema.ACTIVE.name,
                    'storage': {'location_uri': f'http://anything.com/{dataset.code}/obj/path'},
                }
            ],
        },
    )

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    httpx_mock.add_response(
        method='DELETE',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )

    payload = {'operator': 'admin', 'notes': 'testing', 'version': '2.0'}
    res = await client.post(f'/v1/dataset/{dataset_id}/publish', json=payload, headers=authorization_header)
    assert res.status_code == 200
    assert res.json()['result']['status_id'] == dataset_id
    versions = (await db_session.execute(select(Version))).scalars().all()

    assert len(versions) == 1

    _, bucket, version_folder, file = versions[0].location.split('//')[2].split('/')
    assert bucket == dataset.code
    assert version_folder == 'versions'
    assert file.endswith('.zip')

    res = await client.get(f'/v1/dataset/{dataset_id}/publish/status?status_id={dataset_id}')
    assert res.json()['result']['status'] == 'success'
    mock_activity_log.assert_called_with(versions[0])


async def test_publish_version_with_large_notes_should_return_422(client, dataset_factory):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    payload = {'operator': 'admin', 'notes': ''.join(['12345' for i in range(60)]), 'version': '2.0'}
    res = await client.post(f'/v1/dataset/{dataset_id}/publish', json=payload)
    assert res.status_code == 422
    assert res.json() == {
        'detail': [
            {
                'ctx': {'limit_value': 250},
                'loc': ['body', 'notes'],
                'msg': 'ensure this value has at most 250 characters',
                'type': 'value_error.any_str.max_length',
            }
        ]
    }


async def test_publish_version_with_incorrect_notes_should_return_422(client, dataset_factory):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    payload = {'operator': 'admin', 'notes': 'test', 'version': 'incorrect'}
    res = await client.post(f'/v1/dataset/{dataset_id}/publish', json=payload)
    assert res.status_code == 422
    assert res.json() == {
        'detail': [
            {
                'ctx': {'pattern': '^\\d+\\.\\d+$'},
                'loc': ['body', 'version'],
                'msg': 'string does not match regex "^\\d+\\.\\d+$"',
                'type': 'value_error.str.regex',
            }
        ]
    }


async def test_publish_version_duplicate_should_return_409(client, version_factory, dataset_factory):
    dataset = await dataset_factory.create()
    version = await version_factory.create(dataset_code=dataset.code, dataset_id=dataset.id, created_by=dataset.creator)
    dataset_id = version.dataset_id
    payload = {'operator': 'admin', 'notes': 'test', 'version': version.version}
    res = await client.post(f'/v1/dataset/{dataset_id}/publish', json=payload)
    assert res.status_code == 409
    assert res.json() == {'error': {'code': 'global.already_exists', 'details': 'Target resource already exists'}}


async def test_version_list_should_return_200_and_version_in_result(client, version_factory, dataset_factory):
    dataset = await dataset_factory.create()
    version = await version_factory.create(dataset_code=dataset.code, dataset_id=dataset.id, created_by=dataset.creator)
    dataset_id = version.dataset_id
    res = await client.get('/v1/dataset/versions', query_string={'dataset_id': dataset_id})
    assert res.status_code == 200
    assert res.json()['result'][0] == VersionResponseSchema.from_orm(version).to_payload()


async def test_version_not_published_to_dataset_should_return_404(client, dataset_factory):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    payload = {'version': '2.0'}
    res = await client.get(f'/v1/dataset/{dataset_id}/download/pre', query_string=payload)
    assert res.status_code, 404
    assert res.json() == {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}


async def test_version_list_should_return_200_and_download_hash_as_str(client, version_factory, dataset_factory):
    dataset = await dataset_factory.create()
    version = await version_factory.create(dataset_code=dataset.code, dataset_id=dataset.id, created_by=dataset.creator)
    dataset_id = version.dataset_id
    payload = {'version': version.version}
    res = await client.get(f'/v1/dataset/{dataset_id}/download/pre', query_string=payload)
    assert res.status_code, 200
    assert isinstance(res.json()['result']['source'], str)


async def test_publish_version_when_dataset_not_found_should_return_404(client):
    dataset_id = '5baeb6a1-559b-4483-aadf-ef60519584f3'
    payload = {'operator': 'admin', 'notes': 'test', 'version': '2.0'}
    res = await client.post(f'/v1/dataset/{dataset_id}/publish', json=payload)
    assert res.status_code, 404
    assert res.json() == {'error': {'code': 'dataset.not_found', 'details': 'Dataset is not found'}}


async def test_version_publish_status_not_found_should_return_404(client):
    dataset_id = str(uuid4())
    res = await client.get(f'/v1/dataset/{dataset_id}/publish/status?status_id={dataset_id}')
    assert res.status_code, 404
    assert res.json()['error'] == {'code': 'global.not_found', 'details': 'Requested resource is not found'}
