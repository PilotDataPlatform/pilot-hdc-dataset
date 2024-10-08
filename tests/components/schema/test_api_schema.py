# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock
from uuid import uuid4

import pytest

from dataset.components.activity_log.schemas import ActivityDetailsSchema
from dataset.components.activity_log.schemas import ActivitySchema
from dataset.components.exceptions import NotFound
from dataset.components.schema.activity_log import SchemaDatasetActivityLogService
from dataset.components.schema.schemas import SchemaResponse
from dataset.config import get_settings

pytestmark = pytest.mark.asyncio


async def test_schema_without_template_should_return_404(client, dataset_factory):
    dataset = await dataset_factory.create()
    payload = {
        'name': 'unittestdataset2',
        'dataset_geid': str(dataset.id),
        'tpl_geid': str(uuid4()),
        'standard': 'default',
        'system_defined': True,
        'is_draft': True,
        'content': {},
        'creator': 'admin',
        'activity': [],
    }
    res = await client.post('/v1/schema', json=payload)
    assert res.status_code == 404
    assert res.json() == {
        'error': {'code': 'schema.not_found', 'details': 'Dataset or Schema Template or Schema not found.'}
    }


@mock.patch.object(SchemaDatasetActivityLogService, 'send_schema_create_event')
async def test_schema_should_return_200(
    mock_activity_log, client, schema_template_factory, dataset_factory, schema_crud
):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema_template_id = str(schema_template.id)
    payload = {
        'name': 'unittestdataset',
        'dataset_geid': str(schema_template.dataset_id),
        'tpl_geid': schema_template_id,
        'standard': 'default',
        'system_defined': True,
        'is_draft': True,
        'content': {},
        'creator': 'admin',
        'activity': [{'action': 'CREATE', 'resource': 'Schema', 'detail': {'name': 'essential.schema.json'}}],
    }
    res = await client.post('/v1/schema', json=payload)
    assert res.status_code == 200
    result = res.json()['result']
    assert result['name'] == 'unittestdataset'
    created_schema = await schema_crud.retrieve_by_id(result['geid'])
    mock_activity_log.assert_called_with(created_schema, 'admin')


async def test_create_duplicate_schema_return_409(client, dataset_factory, schema_template_factory, schema_factory):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema = await schema_factory.create(dataset_id=str(dataset.id), schema_template_id=str(schema_template.id))

    dataset_id = str(schema.dataset_id)
    schema_template_id = str(schema.schema_template_id)
    payload = {
        'name': schema.name,
        'dataset_geid': dataset_id,
        'tpl_geid': schema_template_id,
        'standard': 'default',
        'system_defined': True,
        'is_draft': True,
        'content': {},
        'creator': 'admin',
        'activity': [{'action': 'CREATE', 'resource': 'Schema', 'detail': {'name': 'essential.schema.json'}}],
    }
    res = await client.post('/v1/schema', json=payload)
    assert res.status_code == 409
    assert res.json()['error'] == {'code': 'global.already_exists', 'details': 'Target resource already exists'}


async def test_get_schema_should_return_200(client, dataset_factory, schema_template_factory, schema_factory):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema = await schema_factory.create(dataset_id=str(dataset.id), schema_template_id=str(schema_template.id))

    schema_id = str(schema.id)
    res = await client.get(f'/v1/schema/{schema_id}')
    assert res.status_code == 200
    assert res.json()['result'] == SchemaResponse.from_orm(schema).to_payload()


async def test_get_schema_not_found_should_return_404(client):
    schema_id = str(uuid4())
    res = await client.get(f'/v1/schema/{schema_id}')
    assert res.status_code == 404
    assert res.json()['error'] == {'code': 'global.not_found', 'details': 'Requested resource is not found'}


@mock.patch.object(SchemaDatasetActivityLogService, 'send_schema_update_event')
async def test_update_schema_should_reflect_change_and_return_200(
    mock_activity_log, client, dataset_factory, schema_template_factory, schema_factory
):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema = await schema_factory.create(dataset_id=str(dataset.id), schema_template_id=str(schema_template.id))

    schema_id = str(schema.id)
    payload = {
        'username': 'admin',
        'content': {'test': 'testing'},
        'activity': [
            {
                'action': 'UPDATE',
                'resource': 'schema',
                'detail': {'name': 'essential.schema.json', 'targets': ['content']},
            }
        ],
    }
    res = await client.put(f'/v1/schema/{schema_id}', json=payload)
    assert res.status_code == 200
    assert res.json()['result']['content'] == {'test': 'testing'}
    mock_activity_log.assert_called_with(
        schema,
        'admin',
        [
            ActivitySchema(
                action='UPDATE',
                resource='schema',
                detail=ActivityDetailsSchema(name='essential.schema.json', targets=['content']),
            )
        ],
    )


@mock.patch.object(SchemaDatasetActivityLogService, 'send_schema_update_event')
async def test_update_essential_schema_should_reflect_change_and_return_200(
    mock_activity_log, client, schema_factory, dataset_factory
):
    dataset = await dataset_factory.create()
    essential_schema = await schema_factory.create_essentials(dataset)
    schema_id = str(essential_schema.id)
    content = {
        'dataset_title': 'title',
        'dataset_authors': ['author'],
        'dataset_description': 'any',
        'dataset_type': 'BIDS',
        'dataset_modality': ['anatomical approach'],
    }
    payload = {
        'username': 'admin',
        'content': content,
        'activity': [],
    }
    res = await client.put(f'/v1/schema/{schema_id}', json=payload)
    assert res.status_code == 200
    assert res.json()['result']['content'] == content
    mock_activity_log.assert_called_with(essential_schema, 'admin', [])


async def test_update_essential_schema_should_have_required_all_fields_return_422(
    client, schema_factory, dataset_factory
):
    dataset = await dataset_factory.create()
    essential_schema = await schema_factory.create_essentials(dataset)
    schema_id = str(essential_schema.id)
    payload = {
        'username': 'admin',
        'content': {'dataset_title': 'title', 'dataset_authors': 'author', 'dataset_description': 'any'},
        'activity': [],
    }
    res = await client.put(f'/v1/schema/{schema_id}', json=payload)
    assert res.status_code == 422
    assert res.json()['error'] == [
        {'detail': 'value is not a valid list', 'source': ['authors'], 'title': 'type_error.list'}
    ]


@mock.patch.object(SchemaDatasetActivityLogService, 'send_schema_delete_event')
async def test_delete_schema_should_return_200(
    mock_activity_log, client, dataset_factory, schema_template_factory, schema_factory, schema_crud
):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    schema = await schema_factory.create(dataset_id=str(dataset.id), schema_template_id=str(schema_template.id))
    dataset_id = str(schema.dataset_id)
    schema_id = str(schema.id)
    payload = {
        'username': 'admin',
        'dataset_geid': dataset_id,
        'activity': [],
    }
    res = await client.delete(f'/v1/schema/{schema_id}', json=payload)
    assert res.status_code == 204
    with pytest.raises(NotFound):
        await schema_crud.retrieve_by_id(schema.id)
    mock_activity_log.assert_called_with(schema, 'admin')


async def test_list_schema_should_bring_essential_schema_first(
    client, dataset_factory, schema_template_factory, schema_factory
):
    settings = get_settings()
    dataset = await dataset_factory.create()
    dataset_id = str(dataset.id)
    essential_schema = await schema_factory.create_essentials(dataset)

    schema_template = await schema_template_factory.create(dataset_id=dataset_id)
    schema_dataset = await schema_factory.create(dataset_id=dataset_id, schema_template_id=str(schema_template.id))

    payload = {
        'dataset_geid': str(schema_dataset.dataset_id),
        'name': settings.ESSENTIALS_NAME,
        'tpl_geid': str(essential_schema.schema_template_id),
    }
    res = await client.post('/v1/schema/list', json=payload)
    assert res.status_code == 200
    assert res.json()['result'][0]['name'] == 'essential.schema.json'
