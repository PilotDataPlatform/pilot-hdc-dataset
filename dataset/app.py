# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import configure_logging
from fastapi import FastAPI

from dataset import __version__
from dataset.config import Settings
from dataset.config import get_settings
from dataset.startup import api_registry
from dataset.startup.exception_handlers import exception_handlers
from dataset.startup.instrument_app import initialize_instrument_app
from dataset.startup.middlewares import middlewares


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title='Service Dataset',
        description='Service to manage datasets',
        debug=settings.DEBUG,
        docs_url='/v1/api-doc',
        redoc_url='/v1/api-redoc',
        version=__version__,
    )

    setup_middlewares(app)
    setup_exception_handlers(app)
    setup_logging(settings)
    api_registry(app)
    setup_instrument_app(app, settings)

    return app


def setup_instrument_app(app: FastAPI, settings: Settings) -> None:
    if settings.OPEN_TELEMETRY_ENABLED:
        initialize_instrument_app(app, settings)


def setup_middlewares(app: FastAPI) -> None:
    """Configure the application middlewares."""

    for middleware in middlewares:
        middleware(app)


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure the application exception handlers."""

    for exc, handler in exception_handlers:
        app.add_exception_handler(exc, handler)


def setup_logging(settings: Settings) -> None:
    """Configure the application logging."""

    configure_logging(settings.LOGGING_LEVEL, settings.LOGGING_FORMAT)
