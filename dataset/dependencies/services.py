# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Request

from dataset.services.metadata import MetadataService
from dataset.services.project import ProjectService
from dataset.services.queue import QueueService


def get_metadata_service(request: Request) -> MetadataService:
    """Return MetadataService instance."""
    return MetadataService(request)


def get_project_service(request: Request):
    """Return instance of ProjectService."""
    return ProjectService(request)


def get_queue_service(request: Request) -> QueueService:
    """Return QueueService instance."""
    return QueueService(request)
