# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock
from uuid import uuid4

from dataset.components.schema_template.activity_log import SchemaTemplateActivityLogService
from dataset.components.schema_template.schemas import SchemaTemplateResponse


@mock.patch.object(SchemaTemplateActivityLogService, 'send_schema_template_on_create_event')
async def test_schema_template_should_return_200(mock_activity_log, client, dataset_factory, schema_template_crud):
    dataset = await dataset_factory.create()
    dataset_id = dataset.id

    payload = {
        'name': 'unittestdataset',
        'standard': 'default',
        'system_defined': True,
        'is_draft': True,
        'content': {},
        'creator': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/schemaTPL', json=payload)
    assert res.status_code == 200
    json_response = res.json()['result']
    assert json_response['name'] == 'unittestdataset'
    retrivied_schema_template = await schema_template_crud.get_template_by_name(json_response['name'])
    mock_activity_log.assert_called_with(retrivied_schema_template, dataset)


async def test_schema_template_duplicate_should_return_code_403(client, schema_template_factory, dataset_factory):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    dataset_id = schema_template.dataset_id
    payload = {
        'name': schema_template.name,
        'standard': 'default',
        'system_defined': True,
        'is_draft': True,
        'content': {},
        'creator': 'admin',
    }
    res = await client.post(f'/v1/dataset/{dataset_id}/schemaTPL', json=payload)
    assert res.status_code == 409
    assert res.json() == {'error': {'code': 'global.already_exists', 'details': 'Target resource already exists'}}


async def test_list_schema_template_by_dataset_id_should_return_200(client, schema_template_factory, dataset_factory):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    dataset_id = schema_template.dataset_id
    payload = {}
    res = await client.post(f'/v1/dataset/{dataset_id}/schemaTPL/list', json=payload)
    assert res.status_code == 200
    assert res.json()['result'][0]['geid'] == str(schema_template.id)


async def test_list_schema_template_when_dataset_id_is_default_should_return_system_defined_templates(
    client, schema_template_factory
):
    expected_system_defined_template_names = {
        'Distribution',
        'Open_minds',
        'Disease',
        'Contributors',
        'Subjects',
        'Grant',
        'Essential',
    }
    await schema_template_factory.truncate_table()
    for template in expected_system_defined_template_names:
        await schema_template_factory.create(name=template, standard='default', system_defined=True, dataset_id=None)

    dataset_id = 'default'
    payload = {}
    res = await client.post(f'/v1/dataset/{dataset_id}/schemaTPL/list', json=payload)
    assert res.status_code == 200
    templates = res.json()['result']
    templates_name = {template['name'] for template in templates}
    system_defined = {template['system_defined'] for template in templates}
    assert templates_name == expected_system_defined_template_names
    assert system_defined == {True}


async def test_get_schema_template_by_id_should_return_200(client, schema_template_factory, dataset_factory):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    res = await client.get(f'/v1/dataset/{schema_template.dataset_id}/schemaTPL/{schema_template.id}')
    assert res.status_code == 200
    assert res.json()['result'] == SchemaTemplateResponse.from_orm(schema_template).to_payload()


@mock.patch.object(SchemaTemplateActivityLogService, 'send_schema_template_on_delete_event')
async def test_delete_schema_template_by_id_should_return_200(
    mock_activity_log, client, schema_template_factory, dataset_factory
):
    dataset = await dataset_factory.create()
    schema_template = await schema_template_factory.create(dataset_id=dataset.id)
    dataset_id = schema_template.dataset_id
    id_ = schema_template.id

    res = await client.delete(f'/v1/dataset/{dataset_id}/schemaTPL/{id_}')
    assert res.status_code == 200
    assert res.json()['result'] == SchemaTemplateResponse.from_orm(schema_template).to_payload()
    mock_activity_log.assert_called_with(schema_template, dataset)


async def test_delete_schema_template_by_id_should_return_404(client):
    res = await client.delete(f'/v1/dataset/{uuid4()}/schemaTPL/{uuid4()}')
    assert res.status_code == 404
    assert res.json() == {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}


async def test_get_schema_template_when_dataset_id_is_default_should_return_system_definied_template(
    client, schema_template_crud, schema_template_factory, settings
):
    await schema_template_factory.truncate_table()
    await schema_template_factory.create(name=settings.ESSENTIALS_TEMPLATE_NAME, system_defined=True, dataset_id=None)

    dataset_id = 'default'
    schema_template = (await schema_template_crud.get_template_by_dataset_or_system_defined('default'))[0]

    res = await client.get(f'/v1/dataset/{dataset_id}/schemaTPL/{schema_template.id}')
    assert res.status_code == 200
    assert res.json()['result'] == SchemaTemplateResponse.from_orm(schema_template).to_payload()
