# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response

from dataset.components.health.dependencies import is_db_connected
from dataset.components.health.dependencies import is_kafka_connected

router = APIRouter(tags=['Internal'])


@router.get(
    '/health',
    summary='Healthcheck if all service dependencies are online.',
    status_code=204,
    responses={204: {'message': ''}, 503: {'description': 'error on database and/or kafka connections'}},
)
async def get_db_status(
    is_db_health: bool = Depends(is_db_connected), is_kafka_health: bool = Depends(is_kafka_connected)
) -> Response:
    """Return response that represents status of the database and kafka connections."""

    if is_db_health and is_kafka_health:
        return Response(status_code=204)
    return Response(status_code=503)
