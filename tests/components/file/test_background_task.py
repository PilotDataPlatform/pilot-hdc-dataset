# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from unittest import mock
from uuid import uuid4

import pytest
import pytest_asyncio

from dataset.components.activity_log.schemas import FileFolderActivityLogSchema
from dataset.components.file.activity_log import FileActivityLogService
from dataset.components.file.dependencies import get_file_crud
from dataset.components.file.dependencies import get_locking_manager
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.file.tasks import FileOperationTasks
from dataset.components.folder.dependencies import get_folder_crud
from dataset.dependencies.s3 import get_s3_client
from dataset.services.task_stream import TaskStreamService

pytestmark = pytest.mark.asyncio

OPER = 'admin'
SESSION_ID = '12345'

folder_lvl1_id = str(uuid4())
folder_lvl2_id = str(uuid4())
folder_lvl3_id = str(uuid4())
folder_lvl4_id = str(uuid4())

root_file = {'id': str(uuid4()), 'parent': None, 'parent_path': None, 'type': 'file', 'name': 'file.txt'}
root_folder = {'id': folder_lvl1_id, 'parent': None, 'parent_path': None, 'type': 'folder', 'name': 'folderlvl1'}

children_file = {
    'id': str(uuid4()),
    'parent': folder_lvl1_id,
    'parent_path': 'folder_lvl1',
    'type': 'file',
    'name': 'file.txt',
}
children_folder = {
    'id': folder_lvl2_id,
    'parent': folder_lvl1_id,
    'parent_path': 'folder_lvl1',
    'type': 'folder',
    'name': 'folder_lvl2',
}
grandchild_folder = {
    'id': folder_lvl3_id,
    'parent': folder_lvl2_id,
    'parent_path': 'folder_lvl1/folder_lvl2',
    'type': 'folder',
    'name': 'folder_lvl3',
}
great_grandchild_folder = {
    'id': folder_lvl4_id,
    'parent': folder_lvl3_id,
    'parent_path': 'folder_lvl1/folder_lvl2/folder_lvl3',
    'type': 'folder',
    'name': 'folder_lvl4',
}


@pytest_asyncio.fixture
def external_requests(httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )


@pytest_asyncio.fixture
async def file_tasks(metadata_service):
    s3_client = await get_s3_client()
    file_crud = await get_file_crud(s3_client, metadata_service)
    folder_crud = await get_folder_crud(s3_client, metadata_service)
    locking_manager = await get_locking_manager(folder_crud)
    task_stream_service = TaskStreamService()
    file_activity_log_service = FileActivityLogService()
    return FileOperationTasks(file_crud, folder_crud, locking_manager, task_stream_service, file_activity_log_service)


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_import')
async def test_copy_file_worker_should_import_file_succeed(
    mock_recursive_lock_import, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_crud, dataset_factory
):
    dataset = await dataset_factory.create()
    source_project_geid = str(uuid4())

    mock_recursive_lock_import.return_value = [], False
    import_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': '077fe46b-3bff-4da3-a4fb-4d6cbf9ce470',
            'parent_path': 'test_folder_6',
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'file',
            'name': 'Dateidaten_für_vretest3',
            'size': 10485760,
            'owner': 'admin',
            'container_code': 'testdataset202201101',
            'container_type': 'dataset',
            'storage': {
                'location_uri': 'minio://http://10.3.7.220/testdataset202201101/data/Dateidaten_für_vretest3',
            },
        }
    ]
    with mock.patch.object(FileOperationTasks, 'recursive_copy') as mock_recursive_copy:
        mock_recursive_copy.return_value = 1, 1, None
        try:
            await file_tasks.copy_files_worker(
                dataset_crud, import_list, dataset, OPER, source_project_geid, 'source_project_code', SESSION_ID
            )
        except Exception as e:
            pytest.fail(f'copy_files_worker raised {e} unexpectedly')
    assert mock_kafka_msg.call_count == 1
    file_folder = FileFolderActivityLogSchema.parse_obj(mock_kafka_msg.call_args[0][0])
    assert file_folder.activity_type == 'import'


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_import')
async def test_copy_file_worker_raise_exception_should_import_file_cancelled(
    mock_recursive_lock_import, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_crud, dataset_factory
):
    dataset = await dataset_factory.create()
    source_project_geid = str(uuid4())
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )
    httpx_mock.add_response(
        method='POST',
        url='http://metadata_service/v1/item/',
        json=[],
    )

    mock_recursive_lock_import.return_value = [], False
    import_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': '077fe46b-3bff-4da3-a4fb-4d6cbf9ce470',
            'parent_path': 'test_folder_6',
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'file',
            'name': 'Dateidaten_für_vretest3',
            'size': 10485760,
            'owner': 'admin',
            'container_code': 'testdataset202201101',
            'container_type': 'dataset',
            'storage': {
                'location_uri': 'minio://http://10.3.7.220/testdataset202201101/data/Dateidaten_für_vretest3',
            },
        }
    ]
    try:
        await file_tasks.copy_files_worker(
            dataset_crud, import_list, dataset, OPER, source_project_geid, 'project_code', SESSION_ID
        )
    except Exception as e:
        pytest.fail(f'copy_files_worker raised {e} unexpectedly')
    content = json.loads(httpx_mock.get_requests()[-1].content)
    assert content['status'] == 'FAILED'


@mock.patch.object(FileActivityLogService, '_message_send')
@pytest.mark.parametrize(
    'target_folder,item_type',
    [
        ({'id': 'any', 'parent': None, 'parent_path': None, 'name': 'any_folder'}, children_file),
        ({'id': None, 'parent': None, 'parent_path': None, 'name': None}, children_file),
        ({'id': 'any', 'parent': None, 'parent_path': None, 'name': 'any_folder'}, children_folder),
        ({'id': None, 'parent': None, 'parent_path': None, 'name': None}, children_folder),
        ({'id': 'any', 'parent': None, 'parent_path': None, 'name': 'any_folder'}, grandchild_folder),
        ({'id': None, 'parent': None, 'name': None, 'parent_path': None}, grandchild_folder),
        ({'id': 'any', 'parent': None, 'parent_path': None, 'name': 'any_folder'}, root_file),
        ({'id': 'any', 'parent': None, 'parent_path': None, 'name': 'any_folder'}, root_folder),
    ],
)
async def test_move_file_worker_should_move_file_succeed(  # noqa: C901
    mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_factory, target_folder, item_type
):
    dataset = await dataset_factory.create()
    code = dataset.code
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
    name = item_type['name']
    if item_type['parent_path']:
        minio_path = item_type['parent_path']
        parent_path = item_type['parent_path']
    else:
        minio_path = name
        parent_path = item_type['name']

    if item_type['type'] == 'folder':
        if item_type['parent_path']:
            minio_path += '/' + name
            parent_path += '.' + name
        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/?'
                f'recursive=true&zone=1&container_code={code}&container_type=dataset&page_size=100&page=0'
            ),
            json={'result': [], 'page': 0, 'num_of_pages': 1},
        )

    move_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': item_type['parent'],
            'parent_path': item_type['parent_path'],
            'restore_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': item_type['type'],
            'name': name,
            'owner': 'admin',
            'container_code': code,
            'container_type': 'dataset',
            'storage': {
                'location_uri': f'minio://http://10.3.7.220/{code}/data/{minio_path}',
            },
        }
    ]

    with mock.patch.object(FileOperationTasks, 'recursive_copy') as mock_recursive_copy:
        mock_recursive_copy.return_value = 1, 1, None
        with mock.patch.object(FileOperationTasks, 'recursive_delete'):
            try:
                await file_tasks.move_file_worker(move_list, dataset, OPER, target_folder, SESSION_ID)
            except Exception as e:
                pytest.fail(f'copy_files_worker raised {e} unexpectedly')
    locks = []
    unlocks = []

    for request in httpx_mock.get_requests():
        if request.url == 'http://data_ops_util/v2/resource/lock/':
            if request.method == 'POST':
                locks.append(json.loads(request.content)['resource_key'])
            else:
                unlocks.append(json.loads(request.content)['resource_key'])

    if item_type['parent_path']:
        parent_path = item_type['parent_path']
        assert f'{code}/data/{minio_path}' in locks
        assert f'{code}/data/{minio_path}' in unlocks
    else:
        assert f'{code}/data/{name}' in locks
        assert f'{code}/data/{name}' in unlocks

    if target_folder['name']:
        target_name = target_folder['name']
        assert f'{code}/data/{target_name}/{name}' in locks
        assert f'{code}/data/{target_name}/{name}' in unlocks
    else:
        assert f'{code}/data/{name}' in locks
        assert f'{code}/data/{name}' in unlocks

    assert mock_kafka_msg.call_count == 1
    file_folder = FileFolderActivityLogSchema.parse_obj(mock_kafka_msg.call_args[0][0])
    assert file_folder.activity_type == 'update'


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_delete')
async def test_delete_files_work_should_delete_file_succeed(
    mock_recursive_lock_delete, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_crud, dataset_factory
):
    dataset = await dataset_factory.create()
    mock_recursive_lock_delete.return_value = [], False
    delete_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': '077fe46b-3bff-4da3-a4fb-4d6cbf9ce470',
            'parent_path': 'test_folder_6',
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'file',
            'name': 'Dateidaten_für_vretest3',
            'size': 10485760,
            'owner': 'admin',
            'container_code': 'testdataset202201101',
            'container_type': 'dataset',
            'storage': {
                'location_uri': 'minio://http://10.3.7.220/testdataset202201101/data/Dateidaten_für_vretest3',
            },
        }
    ]

    with mock.patch.object(FileOperationTasks, 'recursive_delete') as mock_recursive_delete:
        mock_recursive_delete.return_value = 1, 1
        try:
            await file_tasks.delete_files_work(dataset_crud, delete_list, dataset, OPER, SESSION_ID)
        except Exception as e:
            pytest.fail(f'copy_delete_work raised {e} unexpectedly')

    assert mock_kafka_msg.call_count == 1
    file_folder = FileFolderActivityLogSchema.parse_obj(mock_kafka_msg.call_args[0][0])
    assert file_folder.activity_type == 'delete'


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_delete')
async def test_delete_files_work_should_delete_folder_succeed(
    mock_recursive_lock_delete, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_crud, dataset_factory
):
    dataset = await dataset_factory.create()
    mock_recursive_lock_delete.return_value = [], False
    delete_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': None,
            'parent_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'folder',
            'name': 'folder1',
            'size': 10485760,
            'owner': 'admin',
            'container_code': 'testdataset202201101',
            'container_type': 'dataset',
        }
    ]

    with mock.patch.object(FileOperationTasks, 'recursive_delete') as mock_recursive_delete:
        mock_recursive_delete.return_value = 1, 1
        try:
            await file_tasks.delete_files_work(dataset_crud, delete_list, dataset, OPER, SESSION_ID)
        except Exception as e:
            pytest.fail(f'copy_delete_work raised {e} unexpectedly')

    assert mock_kafka_msg.call_count == 1
    file_folder = FileFolderActivityLogSchema.parse_obj(mock_kafka_msg.call_args[0][0])
    assert file_folder.activity_type == 'delete'


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_delete')
async def test_delete_files_work_when_exception_raised_should_delete_folder_cancelled(
    mock_recursive_lock_delete, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_crud, dataset_factory
):
    dataset = await dataset_factory.create()
    mock_recursive_lock_delete.return_value = [], False
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )
    delete_list = [
        {
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': None,
            'parent_path': None,
            'status': ItemStatusSchema.ACTIVE.name,
            'type': 'folder',
            'name': 'folder1',
            'size': 10485760,
            'owner': 'admin',
            'container_code': 'testdataset202201101',
            'container_type': 'dataset',
        }
    ]

    try:
        await file_tasks.delete_files_work(dataset_crud, delete_list, dataset, OPER, SESSION_ID)
    except Exception as e:
        pytest.fail(f'copy_delete_work raised {e} unexpectedly')

    content = json.loads(httpx_mock.get_requests()[-1].content)
    assert content['status'] == 'FAILED'


@mock.patch.object(FileActivityLogService, '_message_send')
@mock.patch('dataset.components.file.locks.LockingManager.recursive_lock_move_rename')
async def test_rename_file_worker_should_rename_file_succeed(
    mock_recursive_lock_move_rename, mock_kafka_msg, external_requests, file_tasks, httpx_mock, dataset_factory
):
    dataset = await dataset_factory.create()
    mock_recursive_lock_move_rename.return_value = [], False
    httpx_mock.add_response(
        method='POST',
        url='http://data_ops_util/v1/task-stream/',
        json={},
    )

    httpx_mock.add_response(
        method='GET',
        url='http://metadata_service/v1/item/077fe46b-3bff-4da3-a4fb-4d6cbf9ce470/',
        json={
            'result': {
                'id': '077fe46b-3bff-4da3-a4fb-4d6cbf9ce470',
                'name': 'folder',
                'container_code': 'source_project_code',
                'parent_path': None,
                'parent': None,
            }
        },
    )

    old_file = {
        'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
        'parent': '077fe46b-3bff-4da3-a4fb-4d6cbf9ce470',
        'parent_path': 'test_folder_6',
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'name': 'Dateidaten_für_vretest3',
        'size': 10485760,
        'owner': 'admin',
        'container_code': f'{dataset.code}',
        'container_type': 'dataset',
        'storage': {
            'location_uri': 'minio://http://10.3.7.220f/{dataset.code}/data/Dateidaten_für_vretest3',
        },
    }
    new_name = 'new_name'

    with mock.patch.object(FileOperationTasks, 'recursive_copy') as mock_recursive_copy:
        mock_recursive_copy.return_value = 1, 1, [{}]
        with mock.patch.object(FileOperationTasks, 'recursive_delete'):
            try:
                await file_tasks.rename_file_worker(old_file, new_name, dataset, OPER, SESSION_ID)
            except Exception as e:
                pytest.fail(f'rename_file_worker raised {e} unexpectedly')

    assert mock_kafka_msg.call_count == 1
    file_folder = FileFolderActivityLogSchema.parse_obj(mock_kafka_msg.call_args[0][0])
    assert file_folder.activity_type == 'update'
