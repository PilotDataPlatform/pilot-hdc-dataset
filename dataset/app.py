# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import configure_logging
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator

from dataset import __version__
from dataset.config import SRV_NAMESPACE
from dataset.config import Settings
from dataset.config import get_settings
from dataset.startup import api_registry
from dataset.startup.exception_handlers import exception_handlers
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
    setup_metrics(app, settings)
    setup_tracing(app, settings)

    return app


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


def setup_metrics(app: FastAPI, settings: Settings) -> None:
    """Instrument the application and expose endpoint for Prometheus metrics."""

    if not settings.ENABLE_PROMETHEUS_METRICS:
        return

    PrometheusFastApiInstrumentator().instrument(app).expose(app, include_in_schema=False)


def setup_tracing(app: FastAPI, settings: Settings) -> None:
    """Instrument the application with OpenTelemetry tracing."""

    if not settings.OPEN_TELEMETRY_ENABLED:
        return

    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: SRV_NAMESPACE}))
    trace.set_tracer_provider(tracer_provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint=f'{settings.OPEN_TELEMETRY_HOST}:{settings.OPEN_TELEMETRY_PORT}', insecure=True
    )

    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
