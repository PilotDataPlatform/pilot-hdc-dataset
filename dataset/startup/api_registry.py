# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI

from dataset.components.bids_result import bids_result_router
from dataset.components.dataset import dataset_router
from dataset.components.file import file_router
from dataset.components.folder import folder_router
from dataset.components.health import health_router
from dataset.components.preview import preview_router
from dataset.components.schema import schema_router
from dataset.components.schema_template import schema_template_router
from dataset.components.version import version_router
from dataset.components.version_sharing import version_sharing_router


def api_registry(app: FastAPI):
    app.include_router(file_router, prefix='/v1')
    app.include_router(version_router, prefix='/v1')
    app.include_router(version_sharing_router, prefix='/v1')
    app.include_router(preview_router, prefix='/v1')
    app.include_router(folder_router, prefix='/v1')
    app.include_router(schema_router, prefix='/v1')
    app.include_router(schema_template_router, prefix='/v1')
    app.include_router(health_router, prefix='/v1')
    app.include_router(bids_result_router, prefix='/v1')
    app.include_router(dataset_router, prefix='/v1')
