# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi.requests import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from redis.asyncio import StrictRedis

from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.dependencies import get_dataset_crud
from dataset.components.exceptions import NotFound
from dataset.components.exceptions import Unauthorized
from dataset.components.file.crud import FileCRUD
from dataset.components.file.dependencies import get_file_crud
from dataset.components.object_storage.s3 import S3Client
from dataset.components.parameters import PageParameters
from dataset.components.parameters import SortParameters
from dataset.components.request.network import Network
from dataset.components.schemas import LegacyResponseSchema
from dataset.components.version.activity_log import VersionActivityLog
from dataset.components.version.activity_log import get_version_activity_log
from dataset.components.version.crud import VersionCRUD
from dataset.components.version.dependencies import get_version_crud
from dataset.components.version.dependencies import get_version_publisher
from dataset.components.version.parameters import VersionFilterParameters
from dataset.components.version.parameters import VersionSortByFields
from dataset.components.version.publisher import VersionPublisher
from dataset.components.version.schemas import VersionCreateSchema
from dataset.components.version.schemas import VersionListResponseSchema
from dataset.components.version.schemas import VersionResponseSchema
from dataset.dependencies.redis import get_redis_client
from dataset.dependencies.s3 import get_s3_client
from dataset.logger import logger

router = APIRouter(prefix='/dataset', tags=['Version'])


@router.post(
    '/{dataset_id}/publish',
    summary='Publish a dataset version',
    response_model=LegacyResponseSchema,
)
async def publish(
    dataset_id: str,
    data: VersionCreateSchema,
    background_tasks: BackgroundTasks,
    dataset_crud: DatasetCRUD = Depends(get_dataset_crud),
    version_crud: VersionCRUD = Depends(get_version_crud),
    version_published: VersionPublisher = Depends(get_version_publisher),
) -> LegacyResponseSchema:
    """Create a version in Minio."""
    await version_crud.check_duplicate_versions(data.version, dataset_id)
    dataset = await dataset_crud.retrieve_by_id(dataset_id)
    await version_published.create_job(str(dataset_id))
    background_tasks.add_task(version_published.publish, dataset.code, dataset.id, data)
    return LegacyResponseSchema(result={'status_id': dataset_id})


@router.get(
    '/{dataset_id}/publish/status',
    summary='Publish status',
    response_model=LegacyResponseSchema,
)
async def publish_status(
    dataset_id: str,
    status_id: str,
    version_crud: VersionCRUD = Depends(get_version_crud),
    redis_client: StrictRedis = Depends(get_redis_client),
) -> LegacyResponseSchema:
    """Get status of publish background task."""
    await version_crud.get_version(dataset_id)
    status = await redis_client.get(status_id)
    if not status:
        raise NotFound()
    return LegacyResponseSchema(result=json.loads(status))


@router.get(
    '/versions',
    response_model=VersionListResponseSchema,
    summary='Get dataset versions',
)
async def list_versions(
    page_parameters: PageParameters = Depends(),
    filter_parameters: VersionFilterParameters = Depends(),
    sort_parameters: SortParameters.with_sort_by_fields(VersionSortByFields) = Depends(),
    version_crud: VersionCRUD = Depends(get_version_crud),
) -> VersionListResponseSchema:
    """Get list of a versions from dataset."""
    filtering = filter_parameters.to_filtering()
    sorting = sort_parameters.to_sorting()
    pagination = page_parameters.to_pagination()

    async with version_crud:
        page = await version_crud.paginate(pagination, sorting, filtering)
    response = VersionListResponseSchema.from_page(page)

    return response


@router.get(
    '/versions/{version_id}',
    response_model=VersionResponseSchema,
    summary='Get dataset version',
)
async def get_version(
    version_id: UUID,
    version_crud: VersionCRUD = Depends(get_version_crud),
) -> VersionResponseSchema:
    """Get specific dataset version."""

    async with version_crud:
        version = await version_crud.retrieve_by_id(version_id)

    return VersionResponseSchema.from_orm(version)


def get_operator(credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]) -> str:
    """Get operator from the authorization header."""

    try:
        payload = jwt.decode(credentials.credentials, options={'verify_signature': False})
        return payload['preferred_username']
    except Exception:
        logger.exception('Failed to get user name from authorization header')
        raise Unauthorized()


def get_network(request: Request) -> Network:
    """Get network from the request headers."""

    return Network.from_headers(request.headers)


@router.get(
    '/{dataset_id}/download/pre',
    summary='Download dataset version',
    response_model=LegacyResponseSchema,
)
async def download_url(
    dataset_id: str,
    version: str,
    version_crud: VersionCRUD = Depends(get_version_crud),
    s3_client: S3Client = Depends(get_s3_client),
    file_crud: FileCRUD = Depends(get_file_crud),
    activity_log: VersionActivityLog = Depends(get_version_activity_log),
    operator: str = Depends(get_operator),
    network: Network = Depends(get_network),
) -> LegacyResponseSchema:
    """Get download url for dataset version."""

    version = await version_crud.get_version(dataset_id, version)
    minio_dict = file_crud._parse_location(version.location)
    presigned_url = await s3_client.get_download_presigned_url(minio_dict['bucket'], minio_dict['path'])
    await activity_log.send_version_download_event(version, operator, network.origin)

    return LegacyResponseSchema(result={'source': presigned_url})
