# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from dataset.components.schema_template.activity_log import SchemaTemplateActivityLogService
from dataset.components.schema_template.activity_log import get_schema_template_activity_log_service
from dataset.components.schema_template.crud import SchemaTemplateCRUD
from dataset.components.schema_template.dependencies import get_schema_template_crud
from dataset.components.schema_template.schemas import LegacySchemaTemplateListResponse
from dataset.components.schema_template.schemas import LegacySchemaTemplateResponse
from dataset.components.schema_template.schemas import SchemaTemplateCreateSchema

router = APIRouter(prefix='/dataset', tags=['Schema Template'])


@router.post(
    '/{dataset_id}/schemaTPL',
    summary='API will create the new schema template',
    response_model=LegacySchemaTemplateResponse,
)
async def create_schema_template(
    dataset_id: UUID,
    request_payload: SchemaTemplateCreateSchema,
    schema_template_crud: SchemaTemplateCRUD = Depends(get_schema_template_crud),
    activity_log: SchemaTemplateActivityLogService = Depends(get_schema_template_activity_log_service),
):
    request_payload.dataset_id = dataset_id
    async with schema_template_crud:
        new_template = await schema_template_crud.create(request_payload)
    await activity_log.send_schema_template_on_create_event(new_template, new_template.dataset)

    return LegacySchemaTemplateResponse(result=new_template)


@router.post(
    '/{dataset_id}/schemaTPL/list',
    summary='API will list the template by condition',
    response_model=LegacySchemaTemplateListResponse,
)
async def list_schema_template(
    dataset_id: UUID | str, schema_template_crud: SchemaTemplateCRUD = Depends(get_schema_template_crud)
):
    templates = await schema_template_crud.get_template_by_dataset_or_system_defined(dataset_id)
    return LegacySchemaTemplateListResponse(result=templates)


@router.get(
    '/{dataset_id}/schemaTPL/{template_id}',
    summary='API will get the template by geid',
    response_model=LegacySchemaTemplateResponse,
)
async def get_schema_template(
    dataset_id: UUID | str,
    template_id: UUID,
    schema_template_crud: SchemaTemplateCRUD = Depends(get_schema_template_crud),
):
    schema_template = await schema_template_crud.retrieve_by_id(template_id)
    return LegacySchemaTemplateResponse(result=schema_template)


@router.delete(
    '/{dataset_id}/schemaTPL/{template_id}',
    summary='API will create the new schema template',
    response_model=LegacySchemaTemplateResponse,
)
async def remove_schema_template(
    dataset_id: UUID,
    template_id: UUID,
    schema_template_crud: SchemaTemplateCRUD = Depends(get_schema_template_crud),
    activity_log: SchemaTemplateActivityLogService = Depends(get_schema_template_activity_log_service),
):
    schema_template = await schema_template_crud.retrieve_by_id(template_id)
    await schema_template_crud.delete(template_id)
    await activity_log.send_schema_template_on_delete_event(schema_template, schema_template.dataset)

    return LegacySchemaTemplateResponse(result=schema_template)
