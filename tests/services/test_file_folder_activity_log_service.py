# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io
from uuid import UUID

from fastavro import schema as avro_schema
from fastavro import schemaless_reader

from dataset.components.activity_log.schemas import FileFolderActivityLogSchema
from dataset.components.file.activity_log import FileActivityLogService
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.folder.activity_log import FolderActivityLog
from dataset.components.folder.schemas import FolderResponseSchema


async def test_send_on_import_event_send_correct_msg(kafka_producer_client, kafka_file_folder_consumer):
    item = {
        'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
        'parent_path': 'test_folder_6',
        'type': 'file',
        'zone': 1,
        'name': 'Dateidaten_für_vretest3',
        'owner': 'admin',
        'container_code': 'testdataset202201101',
        'container_type': 'dataset',
    }
    item_list = [item]
    user = 'user'

    await FileActivityLogService(kafka_producer_client=kafka_producer_client).send_on_import_event(
        'testdataset202201101', 'source_project_code', item_list, user
    )

    msg = await kafka_file_folder_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/metadata.items.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = FileFolderActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.item_id == UUID(item['id'])
    assert activity_log_schema.item_type == item['type']
    assert activity_log_schema.item_name == item['name']
    assert activity_log_schema.item_parent_path == ''
    assert activity_log_schema.container_type == 'dataset'
    assert activity_log_schema.zone == 1
    assert activity_log_schema.imported_from == 'source_project_code'
    assert activity_log_schema.container_code == 'testdataset202201101'
    assert activity_log_schema.user == 'user'
    assert activity_log_schema.activity_type == 'import'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == activity_log['changes']


async def test_send_on_delete_event_send_correct_msg(kafka_producer_client, kafka_file_folder_consumer):
    item = {
        'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
        'parent': 'c4cd9114-358b-4f63-a63f-43767eaecfd9',
        'status': ItemStatusSchema.ACTIVE.name,
        'size': 0,
        'created_time': '2022-03-04 20:31:11.040611',
        'last_updated_time': '2022-03-04 20:31:11.040872',
        'parent_path': 'test_folder_6',
        'type': 'file',
        'zone': 1,
        'name': 'Dateidaten_für_vretest3',
        'owner': 'admin',
        'container_code': 'testdataset202201101',
        'container_type': 'dataset',
    }
    item_list = [item]
    user = 'user'
    await FileActivityLogService(kafka_producer_client=kafka_producer_client).send_on_delete_event(
        'testdataset202201101', item_list, user
    )

    msg = await kafka_file_folder_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/metadata.items.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = FileFolderActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.item_id == UUID(item['id'])
    assert activity_log_schema.item_type == item['type']
    assert activity_log_schema.item_name == item['name']
    assert activity_log_schema.item_parent_path == item['parent_path']
    assert activity_log_schema.container_type == 'dataset'
    assert activity_log_schema.zone == 1
    assert not activity_log_schema.imported_from
    assert activity_log_schema.container_code == 'testdataset202201101'
    assert activity_log_schema.user == 'user'
    assert activity_log_schema.activity_type == 'delete'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == activity_log['changes']


async def test_send_on_move_event_send_correct_msg(kafka_producer_client, kafka_file_folder_consumer):
    item = {
        'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
        'parent_path': 'test_folder_6',
        'type': 'file',
        'zone': 1,
        'name': 'Dateidaten_für_vretest3',
        'owner': 'admin',
        'container_code': 'testdataset202201101',
        'container_type': 'dataset',
    }
    user = 'user'
    await FileActivityLogService(kafka_producer_client=kafka_producer_client).send_on_move_event(
        'testdataset202201101', item, user, '', 'folder1'
    )

    msg = await kafka_file_folder_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/metadata.items.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = FileFolderActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.item_id == UUID(item['id'])
    assert activity_log_schema.item_type == item['type']
    assert activity_log_schema.item_name == item['name']
    assert activity_log_schema.item_parent_path == item['parent_path']
    assert activity_log_schema.container_type == 'dataset'
    assert activity_log_schema.zone == 1
    assert not activity_log_schema.imported_from
    assert activity_log_schema.container_code == 'testdataset202201101'
    assert activity_log_schema.user == 'user'
    assert activity_log_schema.activity_type == 'update'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == [{'item_property': 'parent_path', 'old_value': '', 'new_value': 'folder1'}]


async def test_send_on_rename_event_send_correct_msg(kafka_producer_client, kafka_file_folder_consumer):
    item = {
        'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
        'parent_path': 'test_folder_6',
        'type': 'file',
        'zone': 1,
        'name': 'Dateidaten_für_vretest3',
        'owner': 'admin',
        'container_code': 'testdataset202201101',
        'container_type': 'dataset',
    }
    item_list = [item]
    user = 'user'
    await FileActivityLogService(kafka_producer_client=kafka_producer_client).send_on_rename_event(
        'testdataset202201101', item_list, user, 'file2.txt'
    )

    msg = await kafka_file_folder_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/metadata.items.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = FileFolderActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.item_id == UUID(item['id'])
    assert activity_log_schema.item_type == item['type']
    assert activity_log_schema.item_name == item['name']
    assert activity_log_schema.item_parent_path == item['parent_path']
    assert activity_log_schema.container_type == 'dataset'
    assert activity_log_schema.zone == 1
    assert not activity_log_schema.imported_from
    assert activity_log_schema.container_code == 'testdataset202201101'
    assert activity_log_schema.user == 'user'
    assert activity_log_schema.activity_type == 'update'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == [
        {'item_property': 'name', 'old_value': item['name'], 'new_value': 'file2.txt'}
    ]


async def test_send_create_folder_event_send_correct_msg(kafka_producer_client, kafka_file_folder_consumer):
    folder = FolderResponseSchema(
        **{
            'id': 'ded5bf1e-80f5-4b39-bbfd-f7c74054f41d',
            'parent': 'c4cd9114-358b-4f63-a63f-43767eaecfd9',
            'status': ItemStatusSchema.ACTIVE.name,
            'size': 0,
            'created_time': '2022-03-04 20:31:11.040611',
            'last_updated_time': '2022-03-04 20:31:11.040872',
            'parent_path': 'test_folder_6',
            'type': 'file',
            'zone': 1,
            'name': 'Dateidaten_für_vretest3',
            'owner': 'admin',
            'container_code': 'dataset_code',
            'container_type': 'dataset',
        }
    )

    user = 'user'
    await FolderActivityLog(kafka_producer_client=kafka_producer_client).send_create_folder_event(folder, user)

    msg = await kafka_file_folder_consumer.getone()
    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/metadata.items.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = FileFolderActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.item_id == UUID(folder.id)
    assert activity_log_schema.item_type == folder.type
    assert activity_log_schema.item_name == folder.name
    assert activity_log_schema.item_parent_path == ''
    assert activity_log_schema.container_type == 'dataset'
    assert activity_log_schema.zone == 1
    assert not activity_log_schema.imported_from
    assert activity_log_schema.container_code == 'dataset_code'
    assert activity_log_schema.user == 'user'
    assert activity_log_schema.activity_type == 'create'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == activity_log['changes']
