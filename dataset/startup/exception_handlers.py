# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from dataset.components.exceptions import ServiceException
from dataset.components.exceptions import UnhandledException
from dataset.logger import logger


def service_exception_handler(request: Request, exception: ServiceException) -> JSONResponse:
    """Return the default response structure for service exceptions."""

    return JSONResponse(status_code=exception.status, content={'error': exception.dict()})


def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """Return the default unhandled exception response structure for all unexpected exceptions."""

    logger.exception(f'An exception occurred while processing "{request.url}" url', exc_info=exception)  # noqa: G202
    return service_exception_handler(request, UnhandledException())


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append(
            {
                'title': error.get('type'),
                'detail': error.get('msg'),
                'source': error.get('loc'),
            }
        )
    return JSONResponse(status_code=422, content={'error': errors})


exception_handlers = (
    (ServiceException, service_exception_handler),
    (ValidationError, validation_exception_handler),
    (Exception, unexpected_exception_handler),
)
