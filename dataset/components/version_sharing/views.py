# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response

from dataset.components.parameters import PageParameters
from dataset.components.parameters import SortParameters
from dataset.components.version_sharing.activity_log import VersionSharingActivityLog
from dataset.components.version_sharing.activity_log import get_version_sharing_activity_log
from dataset.components.version_sharing.crud import VersionSharingRequestCRUD
from dataset.components.version_sharing.crud import get_version_sharing_request_crud
from dataset.components.version_sharing.models import VersionSharingRequestStatus
from dataset.components.version_sharing.parameters import VersionSharingRequestFilterParameters
from dataset.components.version_sharing.parameters import VersionSharingRequestSortByFields
from dataset.components.version_sharing.schemas import VersionSharingRequestCreateSchema
from dataset.components.version_sharing.schemas import VersionSharingRequestListResponseSchema
from dataset.components.version_sharing.schemas import VersionSharingRequestResponseSchema
from dataset.components.version_sharing.schemas import VersionSharingRequestStartSchema
from dataset.components.version_sharing.schemas import VersionSharingRequestUpdateSchema
from dataset.dependencies.services import get_queue_service
from dataset.services import QueueService

router = APIRouter(prefix='/version-sharing-requests', tags=['Version Sharing Requests'])


@router.get('/', summary='List all Version Sharing Requests.', response_model=VersionSharingRequestListResponseSchema)
async def list_version_sharing_requests(
    filter_parameters: Annotated[VersionSharingRequestFilterParameters, Depends()],
    sort_parameters: Annotated[SortParameters.with_sort_by_fields(VersionSharingRequestSortByFields), Depends()],
    page_parameters: Annotated[PageParameters, Depends()],
    version_sharing_request_crud: Annotated[VersionSharingRequestCRUD, Depends(get_version_sharing_request_crud)],
) -> VersionSharingRequestListResponseSchema:
    """List all Version Sharing Requests."""

    filtering = filter_parameters.to_filtering()
    sorting = sort_parameters.to_sorting()
    pagination = page_parameters.to_pagination()

    page = await version_sharing_request_crud.paginate(pagination, sorting, filtering)

    return VersionSharingRequestListResponseSchema.from_page(page)


@router.get(
    '/{version_sharing_request_id}',
    summary='Get a Version Sharing Request by id.',
    response_model=VersionSharingRequestResponseSchema,
)
async def get_version_sharing_request_by_id(
    version_sharing_request_id: UUID,
    version_sharing_request_crud: Annotated[VersionSharingRequestCRUD, Depends(get_version_sharing_request_crud)],
) -> VersionSharingRequestResponseSchema:
    """Get a Version Sharing Request by id."""

    version_sharing_request = await version_sharing_request_crud.retrieve_by_id(version_sharing_request_id)

    return VersionSharingRequestResponseSchema.from_orm(version_sharing_request)


@router.post('/', summary='Create a new Version Sharing Request.', response_model=VersionSharingRequestResponseSchema)
async def create_version_sharing_request(
    body: VersionSharingRequestCreateSchema,
    version_sharing_request_crud: Annotated[VersionSharingRequestCRUD, Depends(get_version_sharing_request_crud)],
    version_sharing_activity_log: Annotated[VersionSharingActivityLog, Depends(get_version_sharing_activity_log)],
) -> VersionSharingRequestResponseSchema:
    """Create a new Version Sharing Request."""

    async with version_sharing_request_crud:
        version_sharing_request = await version_sharing_request_crud.create(body)

    await version_sharing_activity_log.send_sharing_request_update(version_sharing_request)

    return VersionSharingRequestResponseSchema.from_orm(version_sharing_request)


@router.patch(
    '/{version_sharing_request_id}',
    summary='Update a Version Sharing Request.',
    response_model=VersionSharingRequestResponseSchema,
)
async def update_version_sharing_request(
    version_sharing_request_id: UUID,
    body: VersionSharingRequestUpdateSchema,
    version_sharing_request_crud: Annotated[VersionSharingRequestCRUD, Depends(get_version_sharing_request_crud)],
    version_sharing_activity_log: Annotated[VersionSharingActivityLog, Depends(get_version_sharing_activity_log)],
) -> VersionSharingRequestResponseSchema:
    """Update a Version Sharing Request."""

    async with version_sharing_request_crud:
        version_sharing_request = await version_sharing_request_crud.update(version_sharing_request_id, body)

    await version_sharing_activity_log.send_sharing_request_update(version_sharing_request)

    return VersionSharingRequestResponseSchema.from_orm(version_sharing_request)


@router.post(
    '/{version_sharing_request_id}/start',
    summary='Start sharing of the Dataset Version specified in Version Sharing Request.',
)
async def start_version_sharing_request(
    version_sharing_request_id: UUID,
    body: VersionSharingRequestStartSchema,
    version_sharing_request_crud: Annotated[VersionSharingRequestCRUD, Depends(get_version_sharing_request_crud)],
    queue_service: Annotated[QueueService, Depends(get_queue_service)],
) -> Response:
    """Start sharing of the Dataset Version specified in Version Sharing Request."""

    version_sharing_request = await version_sharing_request_crud.retrieve_by_id(version_sharing_request_id)

    if version_sharing_request.status is not VersionSharingRequestStatus.ACCEPTED:
        return Response(status_code=400)

    if version_sharing_request.receiver_username is None:
        return Response(status_code=400)

    await queue_service.send_share_dataset_version_message(
        version_sharing_request.version_id,
        version_sharing_request.project_code,
        body.job_id,
        body.session_id,
        version_sharing_request.receiver_username,
    )

    return Response(status_code=204)
