# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.dataset.schemas import DatasetUpdateSchema
from dataset.components.schema.activity_log import SchemaDatasetActivityLogService
from dataset.components.schema.crud import SchemaCRUD
from dataset.components.schema.dependencies import get_schema_crud
from dataset.components.schema.schemas import DELETESchema
from dataset.components.schema.schemas import LegacySchemaListResponse
from dataset.components.schema.schemas import LegacySchemaResponse
from dataset.components.schema.schemas import POSTSchema
from dataset.components.schema.schemas import POSTSchemaList
from dataset.components.schema.schemas import PUTSchema
from dataset.components.schema.schemas import UpdateSchema
from dataset.config import get_settings

settings = get_settings()
router = APIRouter(prefix='/schema', tags=['Schema'])


@router.post('', response_model=LegacySchemaResponse, summary='Create a new schema')
async def create(
    data: POSTSchema,
    schema_crud: SchemaCRUD = Depends(get_schema_crud),
    activity_log: SchemaDatasetActivityLogService = Depends(),
) -> LegacySchemaResponse:
    """Create a new schema."""

    async with schema_crud:
        schema = await schema_crud.create(data)
    api_response = LegacySchemaResponse(result=schema)
    await activity_log.send_schema_create_event(schema, data.creator)

    return api_response


@router.get('/{schema_id}', response_model=LegacySchemaResponse, summary='Get a schema')
async def get(schema_id: UUID, schema_crud: SchemaCRUD = Depends(get_schema_crud)) -> LegacySchemaResponse:
    """Get a schema by id."""

    schema = await schema_crud.retrieve_by_id(schema_id)
    api_response = LegacySchemaResponse(result=schema)
    return api_response


@router.put('/{schema_id}', response_model=LegacySchemaResponse, summary='update a schema')
async def update(
    schema_id: UUID,
    data: PUTSchema,
    schema_crud: SchemaCRUD = Depends(get_schema_crud),
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    activity_log: SchemaDatasetActivityLogService = Depends(),
) -> LegacySchemaResponse:
    """Update a schema."""

    schema = await schema_crud.update(schema_id, UpdateSchema(**data.dict()))
    if schema.name == settings.ESSENTIALS_NAME:
        dataset_schema = DatasetUpdateSchema.from_schema(schema.content)
        await dataset_crud.update(schema.dataset.id, dataset_schema)

    await activity_log.send_schema_update_event(schema, data.username, data.activity)
    api_response = LegacySchemaResponse(result=schema)
    return api_response


@router.delete('/{schema_id}', summary='Delete a schema')
async def delete(
    schema_id: UUID,
    data: DELETESchema,
    schema_crud: SchemaCRUD = Depends(get_schema_crud),
    activity_log: SchemaDatasetActivityLogService = Depends(),
) -> Response:
    """Delete a schema."""

    schema = await schema_crud.retrieve_by_id(schema_id)
    await schema_crud.delete(schema_id)
    await activity_log.send_schema_delete_event(schema, data.username)

    return Response(status_code=204)


@router.post('/list', response_model=LegacySchemaListResponse, summary='API will list the schema by condition')
async def list_schema(
    request_payload: POSTSchemaList, schema_crud: SchemaCRUD = Depends(get_schema_crud)
) -> LegacySchemaListResponse:
    """List schemas by condition."""

    schema_list = await schema_crud.get_schema_list(request_payload)
    api_response = LegacySchemaListResponse(result=schema_list)

    return api_response
