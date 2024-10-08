# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from dataset.components.file.locks import LockingManager
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.folder.crud import FolderCRUD
from dataset.config import get_settings

settings = get_settings()

pytestmark = pytest.mark.asyncio


@pytest.fixture
def folder_crud(s3_test_client, metadata_service) -> FolderCRUD:
    return FolderCRUD(s3_test_client, metadata_service)


@pytest.fixture
def lock_crud(folder_crud) -> LockingManager:
    return LockingManager(folder_crud)


@pytest.mark.parametrize('lock_function,request_method', [('lock_resource', 'POST'), ('unlock_resource', 'DELETE')])
async def test_lock_resource_should_call_resource_lock_correctly(httpx_mock, lock_function, request_method, lock_crud):
    httpx_mock.add_response(
        method=request_method, url='http://data_ops_util/v2/resource/lock/', status_code=200, json={}
    )
    func = getattr(lock_crud, lock_function)
    resp = await func('fake_key', 'me')
    assert not resp


@pytest.mark.parametrize('lock_function,request_method', [('lock_resource', 'POST'), ('unlock_resource', 'DELETE')])
async def test_lock_resource_should_raise_exception_when_lock_request_not_200(
    httpx_mock, lock_function, request_method, lock_crud
):
    httpx_mock.add_response(
        method=request_method, url='http://data_ops_util/v2/resource/lock/', status_code=404, json={}
    )
    with pytest.raises(Exception):
        func = getattr(lock_crud, lock_function)
        await func('fake_key', 'me')


async def test_recursive_lock_import_file_on_root_folder_should_lock_file(httpx_mock, lock_crud):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    dataset_code = 'code'
    nodes = [
        {
            'name': 'file.txt',
            'container_code': 'anyproject',
            'parent_path': 'any_project',
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'file',
            'owner': 'admin',
            'storage': {'location_uri': 'minio://http://10.3.7.220/any_project/core/file.txt'},
        }
    ]
    root_path = settings.DATASET_FILE_FOLDER

    locked_node, error = await lock_crud.recursive_lock_import(dataset_code, nodes, root_path)
    assert not error
    assert locked_node == [('any_project/core/file.txt', 'read')]


async def test_recursive_lock_import_on_root_folder_should_lock_folder(httpx_mock, lock_crud):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_type=project&page_size=100&page=0&container_code=indoctestproject'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent': '84634d30-66aa-4c8b-84f4-ebe3016f59a7',
                    'parent_path': 'admin',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE,
                    'type': 'folder',
                    'name': 'folder1',
                    'owner': 'admin',
                    'container_code': 'indoctestproject',
                    'container_type': 'project',
                },
                {
                    'id': '6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
                    'parent': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent_path': 'admin/folder1',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'file',
                    'name': 'test_file.txt',
                    'owner': 'admin',
                    'container_code': 'indoctestproject',
                    'container_type': 'project',
                    'storage': {
                        'location_uri': 'minio://minio.minio:9000/core-indoctestproject/admin/folder1/test_file.txt',
                    },
                },
            ],
        },
    )
    dataset_code = 'code'
    nodes = [
        {
            'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
            'parent': '84634d30-66aa-4c8b-84f4-ebe3016f59a7',
            'parent_path': 'admin',
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'folder',
            'name': 'folder1',
            'owner': 'admin',
            'container_code': 'indoctestproject',
            'container_type': 'project',
        }
    ]

    root_path = settings.DATASET_FILE_FOLDER

    locked_node, error = await lock_crud.recursive_lock_import(dataset_code, nodes, root_path)
    assert not error
    assert locked_node == [('core-indoctestproject/admin/folder1/test_file.txt', 'read')]


async def test_recursive_lock_import_should_lock_folder(httpx_mock, lock_crud):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_type=project&page_size=100&page=0&container_code=indoctestproject'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent': '84634d30-66aa-4c8b-84f4-ebe3016f59a7',
                    'parent_path': 'admin/folder1',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'folder',
                    'name': 'folder2',
                    'owner': 'admin',
                    'container_code': 'indoctestproject',
                    'container_type': 'project',
                },
                {
                    'id': '6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
                    'parent': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent_path': 'admin/folder1/folder2',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'file',
                    'name': 'test_file.txt',
                    'owner': 'admin',
                    'container_code': 'indoctestproject',
                    'container_type': 'project',
                    'storage': {
                        'location_uri': (
                            'minio://minio.minio:9000/' 'core-indoctestproject/admin/folder1/folder2/test_file.txt'
                        ),
                    },
                },
            ],
        },
    )
    dataset_code = 'code'
    nodes = [
        {
            'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
            'parent': '84634d30-66aa-4c8b-84f4-ebe3016f59a7',
            'parent_path': 'admin/folder1',
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'folder',
            'name': 'folder2',
            'owner': 'admin',
            'container_code': 'indoctestproject',
            'container_type': 'project',
        }
    ]

    root_path = settings.DATASET_FILE_FOLDER

    locked_node, error = await lock_crud.recursive_lock_import(dataset_code, nodes, root_path)
    assert not error
    assert locked_node == [
        ('core-indoctestproject/folder1/folder2', 'read'),
        ('core-indoctestproject/admin/folder1/folder2/test_file.txt', 'read'),
    ]


async def test_recursive_lock_delete_file_on_root_folder_should_lock_file(httpx_mock, lock_crud):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    nodes = [
        {
            'name': 'file.txt',
            'container_code': 'anydataset',
            'status': ItemStatusSchema.ACTIVE.name,
            'parent_path': '',
            'type': 'file',
            'owner': 'admin',
            'storage': {'location_uri': 'minio://http://10.3.7.220/anydataset/data/file.txt'},
        }
    ]
    locked_node, error = await lock_crud.recursive_lock_delete(nodes)
    assert not error
    assert locked_node == [('anydataset/data/file.txt', 'write')]


@pytest.mark.parametrize('folder_parent_path', [(None), ('root_folder')])
async def test_recursive_lock_delete_folder_should_lock_folder_and_their_file(
    folder_parent_path, httpx_mock, lock_crud
):
    minio_path = ''
    if folder_parent_path:
        minio_path = f'{folder_parent_path}/'

    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v2/resource/lock/',
        json={},
    )
    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/?'
            'recursive=true&zone=1&container_type=dataset&page_size=100&page=0&container_code=anydataset'
        ),
        json={
            'page': 0,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent': None,
                    'parent_path': folder_parent_path,
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'folder',
                    'name': 'folder1',
                    'owner': 'admin',
                    'container_code': 'anydataset',
                    'container_type': 'dataset',
                },
                {
                    'id': '6e3305af-859f-4f6a-a3ff-a23a6ab1b9a5',
                    'parent': 'fd571f18-a62a-44b1-927c-91ad662260ac',
                    'parent_path': f'{folder_parent_path}/folder1',
                    'restore_path': None,
                    'status': ItemStatusSchema.ACTIVE.name,
                    'type': 'file',
                    'name': 'test_file.txt',
                    'owner': 'admin',
                    'container_code': 'anydataset',
                    'container_type': 'dataset',
                    'storage': {
                        'location_uri': f'minio://minio.minio:9000/anydataset/data/{minio_path}folder1/test_file.txt',
                    },
                },
            ],
        },
    )
    nodes = [
        {
            'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
            'parent': None,
            'parent_path': folder_parent_path,
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'folder',
            'name': 'folder1',
            'owner': 'admin',
            'container_code': 'anydataset',
            'container_type': 'dataset',
        }
    ]

    locked_node, error = await lock_crud.recursive_lock_delete(nodes)
    assert not error
    assert locked_node == [
        (f'anydataset/data/{minio_path}folder1', 'write'),
        (f'anydataset/data/{minio_path}folder1/test_file.txt', 'write'),
    ]
