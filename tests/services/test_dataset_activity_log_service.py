# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io

import pytest
from fastavro import schema as avro_schema
from fastavro import schemaless_reader

from dataset.components.activity_log.schemas import ActivitySchema
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.dataset.activity_log import DatasetActivityLog
from dataset.components.schema.activity_log import SchemaDatasetActivityLogService
from dataset.components.schema_template.activity_log import SchemaTemplateActivityLogService
from dataset.components.version.activity_log import VersionActivityLog
from dataset.config import get_settings

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def kafka(monkeypatch, kafka_url):
    settings = get_settings()
    monkeypatch.setattr(settings, 'KAFKA_URL', kafka_url)


async def test_send_dataset_on_create_event_should_send_correct_msg(dataset_factory, kafka_dataset_consumer):
    dataset = await dataset_factory.create()
    dataset_activity_log = DatasetActivityLog()

    await dataset_activity_log.send_dataset_on_create_event(dataset)

    msg = await kafka_dataset_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/dataset.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = DatasetActivityLogSchema.parse_obj(activity_log)

    assert not activity_log_schema.version
    assert activity_log_schema.container_code == dataset.code
    assert activity_log_schema.user == dataset.creator
    assert not activity_log_schema.target_name
    assert activity_log_schema.activity_type == 'create'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == activity_log['changes']


@pytest.mark.parametrize(
    'method,change,activity',
    [
        (SchemaTemplateActivityLogService().send_schema_template_on_delete_event, [], 'template_delete'),
        (SchemaTemplateActivityLogService().send_schema_template_on_create_event, [], 'template_create'),
    ],
)
async def test_send_schema_template_events_send_correct_msg(
    kafka_dataset_consumer, schema_template_factory, dataset_factory, method, change, activity
):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    if change:
        await method(schema_template, schema_template.dataset, change)
    else:
        await method(schema_template, schema_template.dataset)

    msg = await kafka_dataset_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/dataset.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = DatasetActivityLogSchema.parse_obj(activity_log)

    assert not activity_log_schema.version
    assert activity_log_schema.container_code == schema_template.dataset.code
    assert activity_log_schema.user == schema_template.creator
    assert not activity_log_schema.version
    assert activity_log_schema.target_name == schema_template.name
    assert activity_log_schema.activity_type == activity
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == change


async def test_send_publish_version_succeed_should_send_correct_msg(
    dataset_factory, version_factory, kafka_dataset_consumer
):
    dataset = await dataset_factory.create()
    version = await version_factory.create(dataset_code=dataset.code, dataset_id=dataset.id, created_by=dataset.creator)
    version_activity_log = VersionActivityLog()
    await version_activity_log.send_publish_version_succeed(version)

    msg = await kafka_dataset_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/dataset.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = DatasetActivityLogSchema.parse_obj(activity_log)

    assert activity_log_schema.version == version.version
    assert activity_log_schema.container_code == version.dataset.code
    assert activity_log_schema.user == version.dataset.creator
    assert not activity_log_schema.target_name
    assert activity_log_schema.activity_type == 'release'
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == activity_log['changes']


@pytest.mark.parametrize(
    'method,change,activity,username',
    [
        (SchemaDatasetActivityLogService().send_schema_delete_event, [], 'schema_delete', 'user'),
        (
            SchemaDatasetActivityLogService().send_schema_update_event,
            [
                ActivitySchema(
                    **{
                        'action': 'UPDATE',
                        'resource': 'schema',
                        'detail': {'name': 'essential.schema.json', 'targets': ['content']},
                    }
                )
            ],
            'schema_update',
            'user',
        ),
        (SchemaDatasetActivityLogService().send_schema_create_event, [], 'schema_create', 'user'),
    ],
)
async def test_send_schema_events_send_correct_msg(
    kafka_dataset_consumer, method, change, activity, username, dataset_factory, schema_template_factory, schema_factory
):

    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema = await schema_factory.create(dataset_id=str(dataset.id), schema_template_id=str(schema_template.id))

    if change:
        await method(schema, username, change)
        changes = change[0].get_changes()
    else:
        await method(schema, username)
        changes = []

    msg = await kafka_dataset_consumer.getone()

    schema_loaded = avro_schema.load_schema('dataset/components/activity_log/dataset.activity.avsc')
    activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

    activity_log_schema = DatasetActivityLogSchema.parse_obj(activity_log)

    assert not activity_log_schema.version
    assert activity_log_schema.container_code == schema.dataset.code
    assert activity_log_schema.user == username
    assert not activity_log_schema.version
    assert activity_log_schema.target_name == schema.name
    assert activity_log_schema.activity_type == activity
    assert activity_log_schema.activity_time == activity_log['activity_time']
    assert activity_log_schema.changes == changes
