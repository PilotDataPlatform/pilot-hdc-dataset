# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Union
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from dataset.components.dataset.activity_log import DatasetActivityLog
from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.dataset.dependencies import get_object_storage_manager
from dataset.components.dataset.exceptions import DatasetCodeConflict
from dataset.components.dataset.object_storage_manager import ObjectStorageManager
from dataset.components.dataset.parameters import DatasetFilterParameters
from dataset.components.dataset.parameters import DatasetSortByFields
from dataset.components.dataset.schemas import DatasetListResponseSchema
from dataset.components.dataset.schemas import DatasetResponseSchema
from dataset.components.dataset.schemas import DatasetSchema
from dataset.components.exceptions import NotFound
from dataset.components.exceptions import UnhandledException
from dataset.components.object_storage.policy import PolicyManager
from dataset.components.object_storage.policy import get_policy_manager
from dataset.components.parameters import PageParameters
from dataset.components.parameters import SortParameters
from dataset.components.schema.crud import SchemaCRUD
from dataset.components.schema.dependencies import get_schema_crud

router = APIRouter(prefix='/datasets', tags=['Datasets'])


@router.post('/', response_model=DatasetResponseSchema, summary='Create a dataset.')
async def create_dataset(
    request_payload: DatasetSchema,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    policy_manager: PolicyManager = Depends(get_policy_manager),
    object_storage_manager: ObjectStorageManager = Depends(get_object_storage_manager),
    schema_crud: SchemaCRUD = Depends(get_schema_crud),
    activity_log: DatasetActivityLog = Depends(),
):
    """dataset creation api."""
    try:
        async with dataset_crud:
            await dataset_crud.retrieve_by_code(request_payload.code)
        raise DatasetCodeConflict()
    except NotFound:
        async with dataset_crud:
            dataset = await dataset_crud.create(request_payload)
        try:
            await object_storage_manager.create_bucket(bucket_name=dataset.code)
            await policy_manager.update_or_create_policies(dataset.code, dataset.creator)
            await schema_crud.create_essentials(dataset)
        # rolling back in case of exception
        except Exception:
            await policy_manager.rollback_policies(dataset.creator)
            await object_storage_manager.remove_bucket(bucket_name=dataset.code)
            await dataset_crud.delete(dataset.id)
            raise UnhandledException()
        await activity_log.send_dataset_on_create_event(dataset)
        return dataset


@router.get('/{dataset_id}', summary='Get a dataset by id or code.', response_model=DatasetResponseSchema)
async def get_dataset(
    dataset_id: Union[UUID, str], dataset_crud: DatasetCRUD = Depends(get_dataset_crud)
) -> DatasetResponseSchema:
    """Get a dataset by id or code."""

    async with dataset_crud:
        dataset = await dataset_crud.retrieve_by_id_or_code(dataset_id)

    return dataset


@router.get('/', summary='List all datasets.', response_model=DatasetListResponseSchema)
async def list_datasets(
    page_parameters: PageParameters = Depends(),
    filter_parameters: DatasetFilterParameters = Depends(),
    sort_parameters: SortParameters.with_sort_by_fields(DatasetSortByFields) = Depends(),
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
) -> DatasetListResponseSchema:
    """List all datasets."""

    filtering = filter_parameters.to_filtering()
    sorting = sort_parameters.to_sorting()
    pagination = page_parameters.to_pagination()

    async with dataset_crud:
        page = await dataset_crud.paginate(pagination, sorting, filtering)

    response = DatasetListResponseSchema.from_page(page)

    return response
