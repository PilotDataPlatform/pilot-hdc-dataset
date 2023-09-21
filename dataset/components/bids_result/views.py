# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends

from dataset.components.bids_result.crud import BIDSResultCRUD
from dataset.components.bids_result.dependencies import get_bids_result_crud
from dataset.components.bids_result.schemas import BIDSResultResponseSchema
from dataset.components.bids_result.schemas import BIDSResultSchema
from dataset.components.bids_result.schemas import LegacyBIDSResultResponseSchema
from dataset.components.bids_result.schemas import UpdateBIDSResultSchema
from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.schemas import LegacyResponseSchema
from dataset.dependencies.services import get_queue_service
from dataset.services import QueueService

router = APIRouter(prefix='/dataset', tags=['Datasets', 'BIDS'])


@router.post('/verify/pre', summary='Pre verify a bids for dataset.', response_model=LegacyResponseSchema)
async def pre_verify_dataset(
    request_payload: BIDSResultSchema,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    queue_service: QueueService = Depends(get_queue_service),
) -> LegacyResponseSchema:
    """Start the BIDS verification sending a msg to queue service."""

    dataset = await dataset_crud.retrieve_by_code(request_payload.dataset_code)
    result = await queue_service.send_message(dataset.code)
    return LegacyResponseSchema(result=result)


@router.get(
    '/bids-msg/{dataset_code}',
    summary='Get bids verification results for dataset.',
    response_model=LegacyBIDSResultResponseSchema,
)
async def get_bids_msg(
    dataset_code: str, bids_result_crud: BIDSResultCRUD = Depends(get_bids_result_crud)
) -> LegacyBIDSResultResponseSchema:
    """Retrieve BIDS results by dataset code."""

    bids_result = await bids_result_crud.retrieve_by_dataset_code(dataset_code)
    return LegacyBIDSResultResponseSchema(result=bids_result)


@router.put(
    '/bids-result/{dataset_code}',
    summary='Update the bids verification results for dataset',
    response_model=BIDSResultResponseSchema,
)
async def update_bids_result(
    dataset_code: str,
    request_payload: UpdateBIDSResultSchema,
    bids_result_crud: BIDSResultCRUD = Depends(get_bids_result_crud),
) -> LegacyBIDSResultResponseSchema:
    """Retrieve BIDS results by dataset code."""

    bids_result = await bids_result_crud.create_or_update_result(dataset_code, request_payload)
    return bids_result
