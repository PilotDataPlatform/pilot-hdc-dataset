# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from copy import deepcopy
from uuid import uuid4

import pytest

from dataset.components.file.schemas import ItemStatusSchema

pytestmark = pytest.mark.asyncio


async def test_import_files_from_source_list_should_return_200(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    source_project = str(dataset.project_id)
    file_id = 'b1064aa6-edbe-4eb6-b560-a8552f2f6162'
    file_dict = {
        'id': file_id,
        'parent': str(uuid4()),
        'parent_path': 'test202203241',
        'name': '.hidden_file.txt',
        'container_code': 'test202203241',
        'container_type': 'project',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'storage': {
            'id': 'f2397e68-4e94-4419-bb72-3be532a789b2',
            'location_uri': (
                'minio://http:///MINIO_ENDPOINT/core-test202203241/admin/test_sub_6'
                ' - Copy/test_sub_delete_6/.hidden_file.txt'
            ),
            'version': None,
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=f'http://project_service/v1/projects/{source_project}',
        json={'code': 'project_code'},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_code=project_code&container_type=project&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [file_dict]},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': []},
    )

    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={'result': {'parent': None}},
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )

    payload = {
        'source_list': [
            file_id,
        ],
        'operator': 'admin',
        'project_geid': source_project,
    }
    res = await client.put(
        f'/v1/dataset/{dataset_geid}/files',
        headers={'Session-ID': 'any', 'Authorization': authorization_header['Authorization']},
        json=payload,
    )

    metadata_request = httpx_mock.get_request(url='http://metadata_service/v1/item/', method='POST')
    metadata_json = json.loads(metadata_request.content)
    assert metadata_json['name'] == file_dict['name']
    assert metadata_json['type'] == file_dict['type']
    assert metadata_json['location_uri'] == f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/.hidden_file.txt'
    assert metadata_json['container_type'] == 'dataset'
    assert metadata_json['container_code'] == dataset.code
    assert metadata_json['zone'] == 1

    result = res.json()['result']
    assert res.status_code == 200
    assert result.get('ignored') == []
    file_dict['parent_path'] = None
    file_dict['parent'] = None

    assert result.get('processing') == [{**file_dict, 'feedback': 'exist'}]


async def test_import_files_from_different_project_return_403(client, dataset_factory):
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    payload = {
        'source_list': [],
        'operator': dataset.creator,
        'project_geid': 'project_2',
    }
    res = await client.put(f'/v1/dataset/{dataset_id}/files', json=payload)
    assert res.status_code == 403


async def test_import_files_from_non_existing_project_return_404(client):
    dataset_id = str(uuid4())
    payload = {
        'source_list': [],
        'operator': 'admin',
        'project_geid': 'NOT_EXIST_Project',
    }
    res = await client.put(f'/v1/dataset/{dataset_id}/files', json=payload)
    assert res.status_code == 404


async def test_import_duplicate_file(client, httpx_mock, dataset_factory, authorization_header):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    source_project = str(dataset.project_id)
    file_id = 'b1064aa6-edbe-4eb6-b560-a8552f2f6162'
    file_dict = {
        'id': file_id,
        'parent': str(uuid4()),
        'parent_path': 'test202203241',
        'name': '.hidden_file.txt',
        'container_code': 'test202203241',
        'container_type': 'project',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'storage': {
            'id': 'f2397e68-4e94-4419-bb72-3be532a789b2',
            'location_uri': (
                'minio://http:///MINIO_ENDPOINT/core-test202203241/admin/test_sub_6'
                ' - Copy/test_sub_delete_6/.hidden_file.txt'
            ),
            'version': None,
        },
    }
    dataset_file = deepcopy(file_dict)
    dataset_file.update({'parent': None, 'parent_path': None})
    httpx_mock.add_response(
        method='GET',
        url=f'http://project_service/v1/projects/{source_project}',
        json={'code': 'project_code'},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_code=project_code&container_type=project&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [file_dict]},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [dataset_file]},
    )

    payload = {
        'source_list': [
            file_id,
        ],
        'operator': 'admin',
        'project_geid': source_project,
    }
    res = await client.put(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)
    result = res.json()['result']
    assert res.status_code == 200
    assert result.get('processing') == []
    assert result.get('ignored') == [{**dataset_file, 'feedback': 'duplicate or unauthorized'}]


async def test_import_files_with_same_name_but_different_types_should_return_200(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    source_project = str(dataset.project_id)
    file_id = 'b1064aa6-edbe-4eb6-b560-a8552f2f6162'
    folder_id = str(uuid4())
    file_dict = {
        'id': file_id,
        'parent': None,
        'parent_path': None,
        'name': '.hidden_file.txt',
        'container_code': 'test202203241',
        'container_type': 'project',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'storage': {
            'id': 'f2397e68-4e94-4419-bb72-3be532a789b2',
            'location_uri': (
                'minio://http:///MINIO_ENDPOINT/core-test202203241/admin/test_sub_6'
                ' - Copy/test_sub_delete_6/.hidden_file.txt'
            ),
            'version': None,
        },
    }
    folder = deepcopy(file_dict)
    folder.update({'id': folder_id, 'type': 'folder', 'storage': {}})
    httpx_mock.add_response(
        method='GET',
        url=f'http://project_service/v1/projects/{source_project}',
        json={'code': 'test202203241'},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_code=test202203241&container_type=project&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [file_dict, folder]},
    )
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
        url='http://metadata_service/v1/item/',
        json={'result': {'parent': None, 'status': ItemStatusSchema.ACTIVE.name}},
    )
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )
    payload = {
        'source_list': [
            folder_id,
        ],
        'operator': 'admin',
        'project_geid': source_project,
    }
    res = await client.put(f'/v1/dataset/{dataset_geid}/files', json=payload, headers=authorization_header)
    result = res.json()['result']
    assert res.status_code == 200
    assert result.get('ignored') == []
    assert result.get('processing') == [{**folder, 'feedback': 'exist'}]


async def test_import_folder_should_import_all_subfolders_and_file(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    project_code = 'test202203241'
    source_project = str(dataset.project_id)

    folder_name_id = str(uuid4())
    folder_lvl1_id = str(uuid4())
    folder_lvl2_id = str(uuid4())
    folder_lvl3_id = str(uuid4())
    file_id = 'b1064aa6-edbe-4eb6-b560-a8552f2f6162'

    folder_lvl1_dict = {
        'id': folder_lvl1_id,
        'parent': folder_name_id,
        'parent_path': 'test202203241/folder1',
        'name': 'folder1',
        'container_code': project_code,
        'container_type': 'project',
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'folder',
    }
    file_dict = {
        'id': file_id,
        'parent': folder_lvl1_id,
        'parent_path': 'test202203241/folder1',
        'name': '.hidden_file.txt',
        'container_code': project_code,
        'container_type': 'project',
        'type': 'file',
        'status': ItemStatusSchema.ACTIVE.name,
        'storage': {
            'location_uri': (f'minio://http:///MINIO_ENDPOINT/core-{project_code}/admin/folder1/' '.hidden_file.txt'),
        },
    }

    httpx_mock.add_response(
        method='GET',
        url=f'http://project_service/v1/projects/{source_project}',
        json={'code': project_code},
    )

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={project_code}&container_type=project&page_size=100&page=0'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': folder_name_id,
                    'parent': None,
                    'parent_path': None,
                    'name': project_code,
                    'container_code': project_code,
                    'container_type': 'project',
                    'type': 'folder_name',
                    'status': ItemStatusSchema.ACTIVE.name,
                },
                {**folder_lvl1_dict},
                {
                    'id': folder_lvl2_id,
                    'parent': folder_lvl1_id,
                    'parent_path': 'test202203241/folder1',
                    'name': 'folder2',
                    'container_code': project_code,
                    'container_type': 'project',
                    'type': 'folder',
                    'status': ItemStatusSchema.ACTIVE.name,
                },
                {
                    'id': folder_lvl3_id,
                    'parent': folder_lvl2_id,
                    'parent_path': 'test202203241/folder1/folder2',
                    'name': 'folder3',
                    'container_code': project_code,
                    'container_type': 'project',
                    'type': 'folder',
                    'status': ItemStatusSchema.ACTIVE.name,
                },
                {**file_dict},
            ],
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            f'recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': []},
    )

    new_folder1_id = str(uuid4())
    folder_1_metadata_payload = json.dumps(
        {
            'parent': None,
            'parent_path': None,
            'type': 'folder',
            'name': 'folder1',
            'owner': 'admin',
            'status': ItemStatusSchema.ACTIVE.name,
            'container_code': dataset.code,
            'container_type': 'dataset',
            'zone': 1,
        }
    )
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'parent': None,
                'parent_path': None,
                'id': new_folder1_id,
                'name': 'folder1',
            }
        },
        match_content=folder_1_metadata_payload.encode(),
    )
    new_folder2_id = str(uuid4())
    folder_2_metadata_payload = json.dumps(
        {
            'parent': new_folder1_id,
            'parent_path': 'folder1',
            'type': 'folder',
            'name': 'folder2',
            'owner': 'admin',
            'status': ItemStatusSchema.ACTIVE.name,
            'container_code': dataset.code,
            'container_type': 'dataset',
            'zone': 1,
        }
    )
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'parent': new_folder1_id,
                'parent_path': 'folder1',
                'id': new_folder2_id,
                'name': 'folder2',
            }
        },
        match_content=folder_2_metadata_payload.encode(),
    )
    new_folder3_id = str(uuid4())
    folder_3_metadata_payload = json.dumps(
        {
            'parent': new_folder2_id,
            'parent_path': 'folder1/folder2',
            'type': 'folder',
            'name': 'folder3',
            'owner': 'admin',
            'status': ItemStatusSchema.ACTIVE.name,
            'container_code': dataset.code,
            'container_type': 'dataset',
            'zone': 1,
        }
    )
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'parent': new_folder2_id,
                'parent_path': 'folder1/folder2',
                'id': new_folder3_id,
                'name': 'folder3',
            }
        },
        match_content=folder_3_metadata_payload.encode(),
    )
    new_file1_id = str(uuid4())
    file_1_metadata_payload = json.dumps(
        {
            'parent': new_folder1_id,
            'parent_path': 'folder1',
            'type': 'file',
            'name': '.hidden_file.txt',
            'owner': 'admin',
            'container_code': dataset.code,
            'container_type': 'dataset',
            'location_uri': f'minio://http://MINIO_ENDPOINT/{dataset.code}/data/folder1/.hidden_file.txt',
            'size': 0,
            'zone': 1,
        }
    )

    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json={
            'result': {
                'parent': new_folder1_id,
                'parent_path': 'folder1',
                'id': new_file1_id,
                'name': '.hidden_file.txt',
            }
        },
        match_content=file_1_metadata_payload.encode(),
    )

    # Kafka queue url.

    # Manage JOB status using Queue Service
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )

    # LOCK & UNLOCK Files/Folder
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json=[],
    )
    httpx_mock.add_response(
        method='DELETE',
        url='http://data_ops_util/v2/resource/lock/',
        json=[],
    )

    payload = {
        'source_list': [
            folder_lvl1_id,
        ],
        'operator': 'admin',
        'project_geid': source_project,
    }
    res = await client.put(
        f'/v1/dataset/{dataset_geid}/files',
        headers={'Session-ID': 'any', 'Authorization': authorization_header['Authorization']},
        json=payload,
    )

    result = res.json()['result']
    assert res.status_code == 200
    assert result.get('ignored') == []
    folder_lvl1_dict['parent_path'] = None
    folder_lvl1_dict['parent'] = None

    assert result.get('processing') == [{**folder_lvl1_dict, 'feedback': 'exist'}]
