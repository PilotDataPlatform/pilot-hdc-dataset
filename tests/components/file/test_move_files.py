# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from unittest import mock
from uuid import uuid4

import pytest

from dataset.components.file.activity_log import FileActivityLogService
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.object_storage.s3 import S3Client


@pytest.fixture
async def background_task_requests(httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
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


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_file_to_folder_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    file_dict = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/164132046.png',
        },
    }
    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder["id"]}/',
        json={'result': folder},
    )

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder, file_dict]},
    )
    moved_file = {
        'id': str(uuid4()),
        'parent': folder['id'],
        'parent_path': 'folder_name',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/folder_name/164132046.png',
        },
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': folder['id'],
                'parent_path': 'folder_name',
                'type': 'file',
                'name': '164132046.png',
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/folder_name/164132046.png',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    payload = {'source_list': [file_dict['id']], 'operator': 'admin', 'target_geid': folder['id']}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [file_dict['id']]
    mock_copy_object.assert_called_with(
        dataset.code, 'data/164132046.png', dataset.code, 'data/folder_name/164132046.png'
    )
    mock_delete_object.assert_called_with(dataset.code, 'data/164132046.png')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**file_dict, 'feedback': 'exist'}, 'admin', '/164132046.png', '/folder_name/164132046.png'
    )


@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_folder_to_a_subfolder_should_create_file_with_correct_data(
    mock_send_on_move_event,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_2 = {
        'id': str(uuid4()),
        'parent': folder['id'],
        'parent_path': folder['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'folder2_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    folder_3 = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder3_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_2["id"]}/',
        json={'result': folder_2},
    )

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder, folder_2, folder_3]},
    )
    moved_folder = {
        'id': str(uuid4()),
        'parent': folder_2['id'],
        'parent_path': f'{folder_2["parent_path"]}/{folder_2["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': 'folder3_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder},
        match_content=json.dumps(
            {
                'parent': moved_folder['parent'],
                'parent_path': moved_folder['parent_path'],
                'type': 'folder',
                'name': moved_folder['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_3["id"]}',
        json={'result': folder_3},
        match_content=b'',
    )

    payload = {'source_list': [folder_3['id']], 'operator': 'admin', 'target_geid': folder_2['id']}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_3['id']]
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**folder_3, 'feedback': 'exist'}, 'admin', '/', '/folder_name/folder2_name/folder3_name'
    )


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_file_to_dataset_root_should_create_new_file_and_remove_old_one(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    parent_folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    file_dict = {
        'id': str(uuid4()),
        'parent': parent_folder_on_root['id'],
        'parent_path': 'folder_name',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/folder_name/164132046.png',
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [parent_folder_on_root, file_dict]},
    )

    moved_file = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/164132046.png',
        },
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': None,
                'parent_path': None,
                'type': 'file',
                'name': '164132046.png',
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/164132046.png',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    payload = {'source_list': [file_dict['id']], 'operator': 'admin', 'target_geid': dataset_id}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [file_dict['id']]
    mock_copy_object.assert_called_with(
        dataset.code, 'data/folder_name/164132046.png', dataset.code, 'data/164132046.png'
    )
    mock_delete_object.assert_called_with(dataset.code, 'data/folder_name/164132046.png')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**file_dict, 'feedback': 'exist'}, 'admin', '/folder_name/164132046.png', '/164132046.png'
    )


async def test_move_wrong_file_ignored_when_relation_doesnt_exist(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    file_id = 'random_geid'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': []},
    )
    payload = {
        'source_list': [file_id],
        'operator': 'admin',
        'target_geid': dataset_id,
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)

    assert res.status_code == 200
    ignored_file = [x.get('id') for x in res.json().get('result').get('ignored')]
    assert ignored_file == [file_id]


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_file_from_a_subfolder_to_another_subfolder_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub1 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub2 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub2',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    file_dict = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/'
                f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/164132046.png'
            ),
        },
    }
    old_file_path = f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/{file_dict["name"]}'

    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_sub2["id"]}/',
        json={'result': folder_sub2},
    )

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder_on_root, folder_sub1, folder_sub2, file_dict]},
    )
    new_file_path = f'{folder_sub2["parent_path"]}/{folder_sub2["name"]}/{file_dict["name"]}'
    moved_file = {
        'id': str(uuid4()),
        'parent': folder_sub2['id'],
        'parent_path': f'{folder_sub2["parent_path"]}/{folder_sub2["name"]}',
        'type': 'file',
        'zone': 1,
        'name': file_dict['name'],
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}'},
    }

    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': folder_sub2['id'],
                'parent_path': f'{folder_sub2["parent_path"]}/{folder_sub2["name"]}',
                'type': 'file',
                'name': file_dict['name'],
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    payload = {'source_list': [file_dict['id']], 'operator': 'admin', 'target_geid': folder_sub2['id']}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [file_dict['id']]
    mock_copy_object.assert_called_with(dataset.code, f'data/{old_file_path}', dataset.code, f'data/{new_file_path}')
    mock_delete_object.assert_called_with(dataset.code, f'data/{old_file_path}')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**file_dict, 'feedback': 'exist'}, 'admin', f'/{old_file_path}', f'/{new_file_path}'
    )


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_subfolder_to_dataset_root_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub1 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    file_dict = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/'
                f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/164132046.png'
            ),
        },
    }
    old_file_path = f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/{file_dict["name"]}'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder_on_root, folder_sub1, file_dict]},
    )
    new_file_path = f'{folder_sub1["name"]}/{file_dict["name"]}'

    moved_folder = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': folder_sub1['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    moved_file = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': moved_folder['name'],
        'type': 'file',
        'zone': 1,
        'name': file_dict['name'],
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}'},
    }
    # move sub1 to root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder},
        match_content=json.dumps(
            {
                'parent': None,
                'parent_path': None,
                'type': 'folder',
                'name': 'sub1',
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub1["id"]}',
        json={'result': folder_sub1},
        match_content=b'',
    )

    # move file to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': moved_file['parent'],
                'parent_path': moved_file['parent_path'],
                'type': 'file',
                'name': moved_file['name'],
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    payload = {'source_list': [folder_sub1['id']], 'operator': 'admin', 'target_geid': dataset_id}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_sub1['id']]
    mock_copy_object.assert_called_with(dataset.code, f'data/{old_file_path}', dataset.code, f'data/{new_file_path}')
    mock_delete_object.assert_called_with(dataset.code, f'data/{old_file_path}')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**folder_sub1, 'feedback': 'exist'}, 'admin', '/', f'/{moved_folder["name"]}'
    )


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_subfolder_with_file_to_subfolder_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub2 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub2',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub1 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    file_dict = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/'
                f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/164132046.png'
            ),
        },
    }
    old_file_path = f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/{file_dict["name"]}'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder_on_root, folder_sub2, folder_sub1, file_dict]},
    )
    new_file_path = f'{folder_sub2["parent_path"]}/{folder_sub2["name"]}/{folder_sub1["name"]}/{file_dict["name"]}'
    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_sub2["id"]}/',
        json={'result': folder_sub2},
    )

    moved_folder = {
        'id': str(uuid4()),
        'parent': folder_sub2['id'],
        'parent_path': f'{folder_sub2["parent_path"]}/{folder_sub2["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': folder_sub1['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    moved_file = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': f'{moved_folder["parent_path"]}/{moved_folder["name"]}',
        'type': 'file',
        'zone': 1,
        'name': file_dict['name'],
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}'},
    }
    # move sub1 to under sub2
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder},
        match_content=json.dumps(
            {
                'parent': moved_folder['parent'],
                'parent_path': moved_folder['parent_path'],
                'type': 'folder',
                'name': moved_folder['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub1["id"]}',
        json={'result': folder_sub1},
        match_content=b'',
    )

    # move file to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': moved_file['parent'],
                'parent_path': moved_file['parent_path'],
                'type': 'file',
                'name': moved_file['name'],
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    payload = {'source_list': [folder_sub1['id']], 'operator': 'admin', 'target_geid': folder_sub2['id']}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_sub1['id']]
    mock_copy_object.assert_called_with(dataset.code, f'data/{old_file_path}', dataset.code, f'data/{new_file_path}')
    mock_delete_object.assert_called_with(dataset.code, f'data/{old_file_path}')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**folder_sub1, 'feedback': 'exist'}, 'admin', 'folder_name', '/folder_name/sub2/sub1'
    )


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_subfolder_with_files_and_folders_to_dataset_root_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub1 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    file_dict = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/'
                f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/164132046.png'
            ),
        },
    }
    old_file_path = f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/{file_dict["name"]}'

    folder_sub2 = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': 'sub2',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [folder_on_root, folder_sub1, file_dict, folder_sub2]},
    )

    moved_folder = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': folder_sub1['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    new_file_path = f'{folder_sub1["name"]}/{file_dict["name"]}'
    moved_file = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': moved_folder['name'],
        'type': 'file',
        'zone': 1,
        'name': file_dict['name'],
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}'},
    }
    moved_folder_sub2 = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': moved_folder['name'],
        'type': 'folder',
        'zone': 1,
        'name': folder_sub2['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    # move sub1 to root
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder},
        match_content=json.dumps(
            {
                'parent': moved_folder['parent'],
                'parent_path': moved_folder['parent_path'],
                'type': 'folder',
                'name': moved_folder['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub1["id"]}',
        json={'result': folder_sub1},
        match_content=b'',
    )

    # move file to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': moved_file['parent'],
                'parent_path': moved_file['parent_path'],
                'type': 'file',
                'name': moved_file['name'],
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    # move sub2 to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder_sub2},
        match_content=json.dumps(
            {
                'parent': moved_folder_sub2['parent'],
                'parent_path': moved_folder_sub2['parent_path'],
                'type': 'folder',
                'name': moved_folder_sub2['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub2["id"]}',
        json={'result': folder_sub2},
        match_content=b'',
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    payload = {'source_list': [folder_sub1['id']], 'operator': 'admin', 'target_geid': dataset_id}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_sub1['id']]
    mock_copy_object.assert_called_with(dataset.code, f'data/{old_file_path}', dataset.code, f'data/{new_file_path}')
    mock_delete_object.assert_called_with(dataset.code, f'data/{old_file_path}')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**folder_sub1, 'feedback': 'exist'}, 'admin', '/', '/sub1'
    )


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
@mock.patch.object(FileActivityLogService, 'send_on_move_event')
async def test_move_subfolder_with_files_and_folders_to_folder_should_create_file_with_correct_data(
    mock_send_on_move_event,
    mock_delete_object,
    mock_copy_object,
    client,
    httpx_mock,
    dataset_factory,
    background_task_requests,
    authorization_header,
):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)

    folder_on_root = {
        'id': str(uuid4()),
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'zone': 1,
        'name': 'folder_name',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    folder_sub3 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub3',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    folder_sub1 = {
        'id': str(uuid4()),
        'parent': folder_on_root['id'],
        'parent_path': folder_on_root['name'],
        'type': 'folder',
        'zone': 1,
        'name': 'sub1',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    file_dict = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/'
                f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/164132046.png'
            ),
        },
    }
    old_file_path = f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}/{file_dict["name"]}'

    folder_sub2 = {
        'id': str(uuid4()),
        'parent': folder_sub1['id'],
        'parent_path': f'{folder_sub1["parent_path"]}/{folder_sub1["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': 'sub2',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
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
            'result': [folder_on_root, folder_sub1, file_dict, folder_sub2, folder_sub3],
        },
    )

    moved_folder = {
        'id': str(uuid4()),
        'parent': folder_sub3['id'],
        'parent_path': f'{folder_sub3["parent_path"]}/{folder_sub3["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': folder_sub1['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }
    new_file_path = f'{moved_folder["parent_path"]}/{moved_folder["name"]}/{file_dict["name"]}'
    moved_file = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': f'{moved_folder["parent_path"]}/{moved_folder["name"]}',
        'type': 'file',
        'zone': 1,
        'name': file_dict['name'],
        'size': 2801,
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}'},
    }
    moved_folder_sub2 = {
        'id': str(uuid4()),
        'parent': moved_folder['id'],
        'parent_path': f'{moved_folder["parent_path"]}/{moved_folder["name"]}',
        'type': 'folder',
        'zone': 1,
        'name': folder_sub2['name'],
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
    }

    # move sub1 to root
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder},
        match_content=json.dumps(
            {
                'parent': moved_folder['parent'],
                'parent_path': moved_folder['parent_path'],
                'type': 'folder',
                'name': moved_folder['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub1["id"]}',
        json={'result': folder_sub1},
        match_content=b'',
    )

    # move file to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_file},
        match_content=json.dumps(
            {
                'parent': moved_file['parent'],
                'parent_path': moved_file['parent_path'],
                'type': 'file',
                'name': moved_file['name'],
                'owner': 'admin',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/{new_file_path}',
                'size': 2801,
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={file_dict["id"]}',
        json={'result': file_dict},
        match_content=b'',
    )

    # move sub2 to sub1 in root level
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': moved_folder_sub2},
        match_content=json.dumps(
            {
                'parent': moved_folder_sub2['parent'],
                'parent_path': moved_folder_sub2['parent_path'],
                'type': 'folder',
                'name': moved_folder_sub2['name'],
                'owner': 'admin',
                'status': 'ACTIVE',
                'container_code': dataset.code,
                'container_type': 'dataset',
                'zone': 1,
            }
        ).encode(),
    )
    httpx_mock.add_response(
        method='DELETE',
        url=f'http://metadata_service/v1/item/?id={folder_sub2["id"]}',
        json={'result': folder_sub2},
        match_content=b'',
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={moved_file["id"]}',
        json={'result': moved_file},
        match_content=json.dumps({'id': moved_file['id'], 'status': 'ACTIVE'}).encode(),
    )

    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{folder_sub3["id"]}/',
        json={'result': folder_sub3},
    )
    payload = {'source_list': [folder_sub1['id']], 'operator': 'admin', 'target_geid': folder_sub3['id']}
    res = await client.post(f'/v1/dataset/{dataset_id}/files', json=payload, headers=authorization_header)
    assert res.status_code == 200
    processing_file = [x.get('id') for x in res.json().get('result').get('processing')]
    assert processing_file == [folder_sub1['id']]
    mock_copy_object.assert_called_with(dataset.code, f'data/{old_file_path}', dataset.code, f'data/{new_file_path}')
    mock_delete_object.assert_called_with(dataset.code, f'data/{old_file_path}')
    mock_send_on_move_event.assert_called_with(
        dataset.code, {**folder_sub1, 'feedback': 'exist'}, 'admin', 'folder_name', '/folder_name/sub3/sub1'
    )
