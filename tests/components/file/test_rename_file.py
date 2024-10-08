# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
import re
from copy import deepcopy
from unittest import mock
from uuid import uuid4

import pytest

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.object_storage.s3 import S3Client

pytestmark = pytest.mark.asyncio


async def test_rename_file_should_add_file_to_processing_and_return_200(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_id = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-1648138467'
    file_dict = {
        'id': file_id,
        'parent': None,
        'parent_path': None,
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': 'testdataset202201111',
        'container_type': 'dataset',
        'created_time': '2022-03-04 20:31:11.040611',
        'last_updated_time': '2022-03-04 20:31:11.040872',
        'storage': {
            'id': '1d6a6897-ff0a-4bb3-96ae-e54ee9d379c3',
            'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png',
            'version': None,
        },
    }
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [file_dict]},
    )

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
    payload = {'new_name': 'new_name', 'operator': 'admin'}
    res = await client.post(f'/v1/dataset/{dataset_geid}/files/{file_id}', json=payload, headers=authorization_header)
    result = res.json()['result']
    assert result['ignored'] == []
    assert result['processing'] == [{**file_dict, 'feedback': 'exist'}]
    assert res.status_code == 200


async def test_rename_file_should_add_file_to_ignoring_when_file_wrong_and_return_200(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_id = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-1648138467'

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': []},
    )

    payload = {'new_name': 'new_name', 'operator': 'admin'}
    res = await client.post(f'/v1/dataset/{dataset_geid}/files/{file_id}', json=payload, headers=authorization_header)
    result = res.json()['result']
    assert result['ignored'] == [
        {
            'id': file_id,
            'feedback': 'unauthorized',
        }
    ]
    assert result['processing'] == []
    assert res.status_code == 200


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
async def test_rename_top_level_folder_keeps_all_subfolders_and_files_order(
    mock_delete_object, mock_copy_object, client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)

    folder_lvl1_id = str(uuid4())
    folder_lvl2_id = str(uuid4())
    folder_lvl3_id = str(uuid4())
    file_id = str(uuid4())

    folder_lvl1_dict = {
        'id': folder_lvl1_id,
        'parent': None,
        'parent_path': None,
        'name': 'folder1',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl2_dict = {
        'id': folder_lvl2_id,
        'parent': folder_lvl1_id,
        'parent_path': 'folder1',
        'name': 'folder2',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl3_dict = {
        'id': folder_lvl3_id,
        'parent': folder_lvl2_id,
        'parent_path': 'folder1/folder2',
        'name': 'folder3',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    file_dict = {
        'id': file_id,
        'parent': folder_lvl3_id,
        'parent_path': 'folder1/folder2/folder3',
        'name': '.hidden_file.txt',
        'container_code': dataset.code,
        'container_type': 'project',
        'type': 'file',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http:///MINIO_ENDPOINT/{dataset.code}/data/folder1/folder2/folder3/.hidden_file.txt'
            ),
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_type=dataset&page_size=100&page=0&container_code={dataset.code}'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {**folder_lvl1_dict},
                {**folder_lvl2_dict},
                {**folder_lvl3_dict},
                {**file_dict},
            ],
        },
    )

    folder_lvl1_dict_new = deepcopy(folder_lvl1_dict)
    folder_lvl1_dict_new['name'] = 'new_name'
    correct_folder_lvl1_request = {
        'parent': None,
        'parent_path': None,
        'type': 'folder',
        'name': 'new_name',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl1_dict_new},
        match_content=json.dumps(correct_folder_lvl1_request).encode(),
    )

    folder_lvl2_dict_new = deepcopy(folder_lvl2_dict)
    folder_lvl2_dict_new['parent_path'] = 'new_name'
    correct_folder_lvl2_request = {
        'parent': folder_lvl1_id,
        'parent_path': 'new_name',
        'type': 'folder',
        'name': 'folder2',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl2_dict_new},
        match_content=json.dumps(correct_folder_lvl2_request).encode(),
    )

    folder_lvl3_dict_new = deepcopy(folder_lvl3_dict)
    folder_lvl3_dict_new['parent_path'] = f'new_name/{folder_lvl2_dict["name"]}'
    correct_folder_lvl3_request = {
        'parent': folder_lvl2_id,
        'parent_path': f'new_name/{folder_lvl2_dict["name"]}',
        'type': 'folder',
        'name': 'folder3',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl3_dict_new},
        match_content=json.dumps(correct_folder_lvl3_request).encode(),
    )

    file_dict_new = deepcopy(file_dict)
    file_dict_new['parent_path'] = f'new_name/{folder_lvl2_dict["name"]}/{folder_lvl3_dict["name"]}'
    file_dict_new['location_uri'] = (
        'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/new_name/folder2/folder3/.hidden_file.txt'
    )
    correct_file_request = {
        'parent': folder_lvl3_id,
        'parent_path': f'new_name/{folder_lvl2_dict["name"]}/{folder_lvl3_dict["name"]}',
        'type': 'file',
        'name': '.hidden_file.txt',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'location_uri': (
            'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/new_name/folder2/folder3/.hidden_file.txt'
        ),
        'size': 0,
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': file_dict_new},
        match_content=json.dumps(correct_file_request).encode(),
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={file_id}',
        json={'result': file_dict_new},
        match_content=json.dumps({'id': file_id, 'status': ItemStatusSchema.ACTIVE.name}).encode(),
    )

    httpx_mock.add_response(method='DELETE', url=re.compile('http://metadata_service/v1/item.*'))

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={**folder_lvl1_dict},
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

    payload = {'new_name': 'new_name', 'operator': 'admin'}

    response = await client.post(
        f'/v1/dataset/{dataset_geid}/files/{folder_lvl1_id}', json=payload, headers=authorization_header
    )
    mock_copy_object.assert_called_with(
        'MINIO_ENDPOINT',
        f'{dataset.code}/data/folder1/folder2/folder3/.hidden_file.txt',
        dataset.code,
        'data/new_name/folder2/folder3/.hidden_file.txt',
    )
    assert response.status_code == 200


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
async def test_rename_middle_level_folder_keeps_all_subfolders_and_files_order(
    mock_delete_object, mock_copy_object, client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)

    folder_lvl1_id = str(uuid4())
    folder_lvl2_id = str(uuid4())
    folder_lvl3_id = str(uuid4())
    file_id = str(uuid4())

    folder_lvl1_dict = {
        'id': folder_lvl1_id,
        'parent': None,
        'parent_path': None,
        'name': 'folder1',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl2_dict = {
        'id': folder_lvl2_id,
        'parent': folder_lvl1_id,
        'parent_path': 'folder1',
        'name': 'folder2',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl3_dict = {
        'id': folder_lvl3_id,
        'parent': folder_lvl2_id,
        'parent_path': 'folder1/folder2',
        'name': 'folder3',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    file_dict = {
        'id': file_id,
        'parent': folder_lvl3_id,
        'parent_path': 'folder1/folder2/folder3',
        'name': '.hidden_file.txt',
        'container_code': dataset.code,
        'container_type': 'project',
        'type': 'file',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/folder1/folder2/folder3/.hidden_file.txt'
            ),
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_type=dataset&page_size=100&page=0&container_code={dataset.code}'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {**folder_lvl1_dict},
                {**folder_lvl2_dict},
                {**folder_lvl3_dict},
                {**file_dict},
            ],
        },
    )

    httpx_mock.add_response(
        method='GET', url=f'http://metadata_service/v1/item/{folder_lvl1_id}/', json={'result': folder_lvl1_dict}
    )

    folder_lvl2_dict_new = deepcopy(folder_lvl2_dict)
    folder_lvl2_dict_new['name'] = 'new_name'
    correct_folder_lvl2_request = {
        'parent': folder_lvl1_id,
        'parent_path': 'folder1',
        'type': 'folder',
        'name': 'new_name',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl2_dict_new},
        match_content=json.dumps(correct_folder_lvl2_request).encode(),
    )

    folder_lvl3_dict_new = deepcopy(folder_lvl3_dict)
    folder_lvl3_dict_new['parent_path'] = f'{folder_lvl1_dict["name"]}/new_name'
    correct_folder_lvl3_request = {
        'parent': folder_lvl2_id,
        'parent_path': f'{folder_lvl1_dict["name"]}/new_name',
        'type': 'folder',
        'name': 'folder3',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl3_dict_new},
        match_content=json.dumps(correct_folder_lvl3_request).encode(),
    )

    file_dict_new = deepcopy(file_dict)
    file_dict_new['parent_path'] = f'{folder_lvl1_dict["name"]}/new_name/{folder_lvl3_dict["name"]}'
    file_dict_new['location_uri'] = (
        'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/new_name/folder2/folder3/.hidden_file.txt'
    )
    correct_file_request = {
        'parent': folder_lvl3_id,
        'parent_path': f'{folder_lvl1_dict["name"]}/new_name/{folder_lvl3_dict["name"]}',
        'type': 'file',
        'name': '.hidden_file.txt',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'location_uri': (
            'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/folder1/new_name/folder3/.hidden_file.txt'
        ),
        'size': 0,
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': file_dict_new},
        match_content=json.dumps(correct_file_request).encode(),
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={file_id}',
        json={'result': file_dict_new},
        match_content=json.dumps({'id': file_id, 'status': ItemStatusSchema.ACTIVE.name}).encode(),
    )

    httpx_mock.add_response(method='DELETE', url=re.compile('http://metadata_service/v1/item.*'))

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={**folder_lvl1_dict},
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

    payload = {'new_name': 'new_name', 'operator': 'admin'}

    # check middle level folder rename
    response = await client.post(
        f'/v1/dataset/{dataset_geid}/files/{folder_lvl2_id}', json=payload, headers=authorization_header
    )
    mock_copy_object.assert_called_with(
        dataset.code,
        'data/folder1/folder2/folder3/.hidden_file.txt',
        dataset.code,
        'data/folder1/new_name/folder3/.hidden_file.txt',
    )
    assert response.status_code == 200


@mock.patch.object(S3Client, 'copy_object')
@mock.patch.object(S3Client, 'delete_object')
async def test_rename_bottom_level_folder_keeps_all_subfolders_and_files_order(
    mock_delete_object, mock_copy_object, client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)

    folder_lvl1_id = str(uuid4())
    folder_lvl2_id = str(uuid4())
    folder_lvl3_id = str(uuid4())
    file_id = str(uuid4())

    folder_lvl1_dict = {
        'id': folder_lvl1_id,
        'parent': None,
        'parent_path': None,
        'name': 'folder1',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl2_dict = {
        'id': folder_lvl2_id,
        'parent': folder_lvl1_id,
        'parent_path': 'folder1',
        'name': 'folder2',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    folder_lvl3_dict = {
        'id': folder_lvl3_id,
        'parent': folder_lvl2_id,
        'parent_path': 'folder1/folder2',
        'name': 'folder3',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    file_dict = {
        'id': file_id,
        'parent': folder_lvl3_id,
        'parent_path': 'folder1/folder2/folder3',
        'name': '.hidden_file.txt',
        'container_code': dataset.code,
        'container_type': 'project',
        'type': 'file',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (
                f'minio://http:///MINIO_ENDPOINT/{dataset.code}/data/folder1/folder2/folder3/.hidden_file.txt'
            ),
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_type=dataset&page_size=100&page=0&container_code={dataset.code}'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {**folder_lvl1_dict},
                {**folder_lvl2_dict},
                {**folder_lvl3_dict},
                {**file_dict},
            ],
        },
    )

    httpx_mock.add_response(
        method='GET', url=f'http://metadata_service/v1/item/{folder_lvl2_id}/', json={'result': folder_lvl2_dict}
    )

    folder_lvl3_dict_new = deepcopy(folder_lvl3_dict)
    folder_lvl3_dict_new['name'] = 'new_name'
    correct_folder_lvl3_request = {
        'parent': folder_lvl2_id,
        'parent_path': 'folder1/folder2',
        'type': 'folder',
        'name': 'new_name',
        'owner': 'admin',
        'status': 'ACTIVE',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': folder_lvl3_dict_new},
        match_content=json.dumps(correct_folder_lvl3_request).encode(),
    )

    file_dict_new = deepcopy(file_dict)
    file_dict_new['parent_path'] = f'{folder_lvl1_dict["name"]}/{folder_lvl2_dict["name"]}/new_name'
    file_dict_new['location_uri'] = (
        'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/new_name/folder2/folder3/.hidden_file.txt'
    )
    correct_file_request = {
        'parent': folder_lvl3_id,
        'parent_path': f'{folder_lvl1_dict["name"]}/{folder_lvl2_dict["name"]}/new_name',
        'type': 'file',
        'name': '.hidden_file.txt',
        'owner': 'admin',
        'container_code': dataset.code,
        'container_type': 'dataset',
        'location_uri': (
            'minio://http://MINIO_ENDPOINT/l6n6g0i4s8i7w6g4n7z5/data/folder1/folder2/new_name/.hidden_file.txt'
        ),
        'size': 0,
        'zone': 1,
    }
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': file_dict_new},
        match_content=json.dumps(correct_file_request).encode(),
    )

    httpx_mock.add_response(
        method='PUT',
        url=f'http://metadata_service/v1/item/?id={file_id}',
        json={'result': file_dict_new},
        match_content=json.dumps({'id': file_id, 'status': ItemStatusSchema.ACTIVE.name}).encode(),
    )

    # collect all DELETE requests
    httpx_mock.add_response(method='DELETE', url=re.compile('http://metadata_service/v1/item.*'))

    # background http calls
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={**folder_lvl1_dict},
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

    payload = {'new_name': 'new_name', 'operator': 'admin'}

    # check bottom level folder rename
    response = await client.post(
        f'/v1/dataset/{dataset_geid}/files/{folder_lvl3_id}', json=payload, headers=authorization_header
    )
    mock_copy_object.assert_called_with(
        'MINIO_ENDPOINT',
        f'{dataset.code}/data/folder1/folder2/folder3/.hidden_file.txt',
        dataset.code,
        'data/folder1/folder2/new_name/.hidden_file.txt',
    )
    assert response.status_code == 200


async def test_rename_file_should_add_file_to_ignoring_when_file_duplicated_and_return_200(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_id = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-1648138467'
    file_dict = {
        'id': file_id,
        'parent': None,
        'parent_path': None,
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'zone': 1,
        'name': '164132046.png',
        'size': 2801,
        'owner': 'admin',
        'container_code': 'testdataset202201111',
        'container_type': 'dataset',
        'created_time': '2022-03-04 20:31:11.040611',
        'last_updated_time': '2022-03-04 20:31:11.040872',
        'storage': {
            'id': '1d6a6897-ff0a-4bb3-96ae-e54ee9d379c3',
            'location_uri': 'minio://http://minio.minio:9000/testdataset202201111/data/164132046.png',
            'version': None,
        },
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
                file_dict,
                {
                    'id': 'f496d010-cb41-4353-bc5b-88f8e03c434d',
                    'name': 'new_name',
                    'parent': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'parent_path': None,
                    'type': 'file',
                },
            ],
        },
    )

    payload = {'new_name': 'new_name', 'operator': 'admin'}
    res = await client.post(f'/v1/dataset/{dataset_geid}/files/{file_id}', json=payload, headers=authorization_header)
    result = res.json()['result']
    assert result['ignored'] == [{**file_dict, 'feedback': 'exist'}]
    assert result['processing'] == []
    assert res.status_code == 200
