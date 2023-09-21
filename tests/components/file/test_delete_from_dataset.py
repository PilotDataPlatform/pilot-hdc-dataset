# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from unittest import mock

import pytest
from common.object_storage_adaptor.boto3_client import Boto3Client

from dataset.components.file.activity_log import FileActivityLogService
from dataset.components.file.schemas import ItemStatusSchema

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def external_requests(httpx_mock):
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


@mock.patch.object(Boto3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_delete_event')
async def test_file_delete_from_dataset_when_file_should_start_background_task_and_return_200(
    mock_send_on_delete_event,
    mock_minio_delete,
    client,
    httpx_mock,
    external_requests,
    dataset_factory,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_id = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067'
    file_dict = {
        'id': file_id,
        'parent': '81b70730-2bc3-4ffc-9e98-3d0cdeec867b',
        'parent_path': 'admin/test_sub_6 - Copy/test_sub_delete_6',
        'name': '.hidden_file.txt',
        'container_code': dataset.code,
        'status': ItemStatusSchema.ACTIVE.name,
        'container_type': 'dataset',
        'type': 'file',
        'storage': {
            'location_uri': (
                'minio://http://minio.minio:9000/core-test202203241/admin/test_sub_6'
                ' - Copy/test_sub_delete_6/.hidden_file.txt'
            )
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'result': [file_dict], 'page': 0, 'num_of_pages': 1},
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_id}',
        json={},
    )

    base_stream_task_payload = {
        'session_id': 'local_test',
        'target_names': ['/'.join([file_dict['parent_path'], file_dict['name']])],
        'target_type': file_dict['type'],
        'container_code': dataset.code,
        'container_type': 'dataset',
        'action_type': 'data_delete',
        'status': 'WAITING',
        'job_id': file_id,
    }
    waiting_stream_task_payload = {**base_stream_task_payload, **{'status': 'WAITING'}}
    running_stream_task_payload = {**base_stream_task_payload, **{'status': 'RUNNING'}}
    succeed_stream_task_payload = {**base_stream_task_payload, **{'status': 'SUCCEED'}}

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(waiting_stream_task_payload).encode(),
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(running_stream_task_payload).encode(),
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(succeed_stream_task_payload).encode(),
    )

    payload = {'source_list': [file_id], 'operator': 'admin'}
    res = await client.delete(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)

    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [file_id]
    mock_send_on_delete_event.assert_called_with(dataset.code, [{**file_dict, 'feedback': 'exist'}], 'admin')


@mock.patch.object(Boto3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_delete_event')
async def test_file_delete_from_dataset_when_folder_should_start_background_task_and_return_200(
    mock_send_on_delete_event,
    mock_minio_delete,
    client,
    httpx_mock,
    dataset_factory,
    external_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    folder_id = 'fd571f18-a62a-44b1-927c-91ad662260ac'
    folder_dict = {
        'id': folder_id,
        'parent': None,
        'parent_path': None,
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
        'name': 'folder1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {**folder_dict},
                {
                    'id': '6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
                    'parent': folder_id,
                    'parent_path': 'folder1',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'file',
                    'name': 'test_file.txt',
                    'owner': 'admin',
                    'container_code': dataset.code,
                    'container_type': 'dataset',
                    'storage': {
                        'location_uri': f'minio://minio.minio:9000/{dataset.code}/data/folder1/test_file.txt',
                    },
                },
            ],
        },
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_id}',
        json={},
    )
    httpx_mock.add_response(
        method='DELETE',
        url='http://metadata_service/v1/item/?id=6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
        json={},
    )

    base_stream_task_payload = {
        'session_id': 'local_test',
        'target_names': [folder_dict['name']],
        'target_type': folder_dict['type'],
        'container_code': dataset.code,
        'container_type': 'dataset',
        'action_type': 'data_delete',
        'status': 'WAITING',
        'job_id': folder_id,
    }
    waiting_stream_task_payload = {**base_stream_task_payload, **{'status': 'WAITING'}}
    running_stream_task_payload = {**base_stream_task_payload, **{'status': 'RUNNING'}}
    succeed_stream_task_payload = {**base_stream_task_payload, **{'status': 'SUCCEED'}}

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(waiting_stream_task_payload).encode(),
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(running_stream_task_payload).encode(),
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
        match_content=json.dumps(succeed_stream_task_payload).encode(),
    )
    payload = {'source_list': [folder_id], 'operator': 'admin'}
    res = await client.delete(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)

    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_id]
    mock_send_on_delete_event.assert_called_with(dataset.code, [{**folder_dict, 'feedback': 'exist'}], 'admin')


@mock.patch.object(Boto3Client, 'delete_object')
async def test_file_delete_from_dataset_when_folder_is_duplicate_should_start_background_task_and_return_200(
    mock_minio_delete, client, httpx_mock, external_requests, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    folder_id = 'fd571f18-a62a-44b1-927c-91ad662260ac'
    folder_dict = {
        'id': folder_id,
        'parent': None,
        'parent_path': None,
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
        'name': 'folder1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {**folder_dict},
                {
                    'id': '6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
                    'parent': folder_id,
                    'parent_path': 'folder1',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'file',
                    'name': 'test_file.txt',
                    'owner': 'admin',
                    'container_code': dataset.code,
                    'container_type': 'dataset',
                    'storage': {
                        'location_uri': f'minio://minio.minio:9000/{dataset.code}/data/folder1/test_file.txt',
                    },
                },
            ],
        },
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_id}',
        json={},
    )
    httpx_mock.add_response(
        method='DELETE',
        url='http://metadata_service/v1/item/?id=6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
        json={},
    )

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )
    payload = {'source_list': [folder_id, folder_id], 'operator': 'admin'}
    res = await client.delete(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)

    assert res.status_code == 200
    assert res.json().get('result').get('processing')[1]['feedback'] == 'duplicate in same batch, update the name'


async def test_delete_from_not_in_dataset_should_not_reaise_error(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_geid = 'random_geid'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [{'id': '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067'}]},
    )

    payload = {'source_list': [file_geid], 'operator': 'admin'}
    res = await client.delete(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    ignored_file = [x.get('id') for x in res.json().get('result').get('ignored')]
    assert ignored_file == [file_geid]
