# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock

import pytest

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.folder.activity_log import FolderActivityLog

pytestmark = pytest.mark.asyncio


@mock.patch.object(FolderActivityLog, '_message_send')
async def test_create_root_folder_should_return_200_and_folder_data(
    mock_kafka_msg, client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    folder_name = 'unitest_folder'
    folder_owner = 'admin'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            f'?recursive=true&zone=1&container_code={dataset.code}&'
            f'container_type=dataset&page_size=100&page=0&name={folder_name}'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': []},
    )

    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'id': '23c98b6d-81d0-4925-9eb4-98617a4ae5f8',
                'parent': None,
                'parent_path': None,
                'restore_path': None,
                'status': ItemStatusSchema.ACTIVE.name,
                'type': 'folder',
                'zone': 0,
                'name': folder_name,
                'size': 0,
                'owner': folder_owner,
                'container_code': dataset.code,
                'container_type': 'dataset',
                'created_time': '2023-01-04 12:43:43.247662',
                'last_updated_time': '2023-01-04 12:43:43.247669',
                'storage': {'id': '4935b741-1f45-4136-bb6f-9450e7a2fb5d', 'location_uri': None, 'version': None},
                'extended': {
                    'id': 'e9ce00eb-505a-4c89-affb-a06b2eb7a671',
                    'extra': {'tags': [], 'system_tags': [], 'attributes': {}},
                },
                'favourite': False,
            }
        },
    )
    payload = {
        'folder_name': folder_name,
        'username': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload, headers=authorization_header)
    assert res.status_code == 200
    assert res.json()['result']['name'] == folder_name
    assert res.json()['result']['container_code'] == dataset.code
    assert res.json()['result']['owner'] == folder_owner

    assert mock_kafka_msg.call_count == 1


async def test_create_duplicate_root_folder_should_return_409(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    new_folder_name = 'unitest_folder'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            f'?recursive=true&zone=1&container_code={dataset.code}&'
            f'container_type=dataset&page_size=100&page=0&&name={new_folder_name}'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'bb72b4a6-d2bb-41fa-acaf-19cb7d4fce0f',
                    'parent': None,
                    'parent_path': None,
                    'name': new_folder_name,
                    'container_code': dataset.code,
                    'container_type': 'dataset',
                    'status': ItemStatusSchema.ACTIVE.name,
                    'size': 10,
                    'owner': 'admin',
                    'created_time': '2022-03-04 20:31:11.040611',
                    'last_updated_time': '2022-03-04 20:31:11.040872',
                    'storage': {
                        'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'
                    },
                }
            ],
        },
    )

    payload = {
        'folder_name': new_folder_name,
        'username': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload, headers=authorization_header)
    assert res.status_code == 409
    assert res.json() == {'error': {'code': 'global.already_exists', 'details': 'Target resource already exists'}}


@mock.patch.object(FolderActivityLog, '_message_send')
async def test_create_sub_folder_should_return_200(
    mock_kafka_msg, client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    folder_id = 'cfa31c8c-ba29-4cdf-b6f2-feef05ec9c12'

    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_id}/',
        json={
            'result': {
                'id': folder_id,
                'type': 'folder',
                'parent': '657694cd-6a1c-4854-bdff-5e5b1d2a999b',
                'parent_path': 'any/test_folder',
                'name': 'test_folder',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'status': ItemStatusSchema.ACTIVE.name,
                'size': 10,
                'owner': 'admin',
                'created_time': '2022-03-04 20:31:11.040611',
                'last_updated_time': '2022-03-04 20:31:11.040872',
                'storage': {'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'},
            }
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            f'?recursive=true&zone=1&container_code={dataset.code}&'
            'container_type=dataset&page_size=100&page=0&name=unitest_folder2'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': folder_id,
                    'parent': '657694cd-6a1c-4854-bdff-5e5b1d2a999b',
                    'type': 'folder',
                    'parent_path': 'any/test_folder',
                    'name': 'test_folder',
                    'container_code': dataset.code,
                    'container_type': 'dataset',
                    'status': ItemStatusSchema.ACTIVE.name,
                    'size': 10,
                    'owner': 'admin',
                    'created_time': '2022-03-04 20:31:11.040611',
                    'last_updated_time': '2022-03-04 20:31:11.040872',
                    'storage': {
                        'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'
                    },
                },
                {
                    'id': '657694cd-6a1c-4854-bdff-5e5b1d2a999b',
                    'parent': None,
                    'parent_path': None,
                    'type': 'folder',
                    'name': 'any',
                    'container_code': dataset.code,
                    'container_type': 'dataset',
                    'status': ItemStatusSchema.ACTIVE.name,
                    'size': 10,
                    'owner': 'admin',
                    'created_time': '2022-03-04 20:31:11.040611',
                    'last_updated_time': '2022-03-04 20:31:11.040872',
                    'storage': {
                        'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'
                    },
                },
            ],
        },
    )

    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'id': 'bb72b4a6-d2bb-41fa-acaf-19cb7d4fce0f',
                'type': 'folder',
                'parent': folder_id,
                'parent_path': 'any/test_folder.unitest_folder2',
                'name': 'unitest_folder2',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'status': ItemStatusSchema.ACTIVE.name,
                'size': 10,
                'owner': 'admin',
                'created_time': '2022-03-04 20:31:11.040611',
                'last_updated_time': '2022-03-04 20:31:11.040872',
                'storage': {'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'},
            }
        },
    )
    payload = {
        'folder_name': 'unitest_folder2',
        'username': 'admin',
        'parent_folder_geid': folder_id,
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload, headers=authorization_header)
    assert res.status_code == 200
    assert res.json()['result'] == {
        'id': 'bb72b4a6-d2bb-41fa-acaf-19cb7d4fce0f',
        'type': 'folder',
        'parent': folder_id,
        'parent_path': 'any/test_folder.unitest_folder2',
        'name': 'unitest_folder2',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'size': 10,
        'owner': 'admin',
        'created_time': '2022-03-04T20:31:11',
        'last_updated_time': '2022-03-04T20:31:11',
        'storage': {'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png'},
    }
    assert mock_kafka_msg.call_count == 1


@pytest.mark.parametrize(
    'folder_name',
    [
        'test\\zame',
        'test/name',
        'test:name',
        'test?name',
        'test*name',
        'test<name',
        'test>name',
        'test|name',
        'test"name',
    ],
)
async def test_create_folder_with_invalid_name_should_return_400(client, folder_name, dataset_factory):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    payload = {
        'folder_name': folder_name,
        'username': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload)
    assert res.status_code == 422
    assert res.json() == {
        'detail': [
            {
                'ctx': {'pattern': '^[^\\\\\\/:?\\*<>|"]+$'},
                'loc': ['body', 'folder_name'],
                'msg': 'string does not match regex "^[^\\\\\\/:?\\*<>|"]+$"',
                'type': 'value_error.str.regex',
            }
        ]
    }


async def test_create_folder_when_dataset_not_found_should_return_404(client):
    dataset_id = '5baeb6a1-559b-4483-aadf-ef60519584f3'
    payload = {
        'folder_name': 'unitest_folder',
        'username': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload)
    assert res.status_code == 404
    assert res.json()['error'] == {'code': 'dataset.not_found', 'details': 'Dataset is not found'}


async def test_create_sub_folder_when_parent_folder_not_found_should_return_404(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    folder_id = 'cfa31c8c-ba29-4cdf-b6f2-feef05ec9c12'
    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_id}/',
        json={'result': {}},
        status_code=404,
    )
    payload = {
        'folder_name': 'unitest_folder',
        'username': 'admin',
        'parent_folder_geid': folder_id,
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload, headers=authorization_header)
    assert res.status_code == 404
    assert res.json()['error'] == {'code': 'global.not_found', 'details': 'Requested resource is not found'}


async def test_create_folder_with_long_folder_name_should_return_422(client, dataset_factory, faker):
    folder_name = faker.pystr(31, 31)
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    payload = {
        'folder_name': folder_name,
        'username': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/folder', json=payload)
    assert res.status_code == 422
    assert res.json() == {
        'detail': [
            {
                'loc': ['body', 'folder_name'],
                'msg': 'ensure this value has at most 20 characters',
                'type': 'value_error.any_str.max_length',
                'ctx': {'limit_value': 20},
            }
        ]
    }
