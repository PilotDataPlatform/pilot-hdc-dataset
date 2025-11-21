# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import UUID

from pydantic import Field

from dataset.components.schemas import BaseSchema
from dataset.components.schemas import ListResponseSchema
from dataset.components.version_sharing.models import VersionSharingRequestStatus


class VersionSharingRequestSchema(BaseSchema):
    """General Version Sharing Request schema."""

    version_id: UUID
    project_code: str
    initiator_username: str
    receiver_username: str | None
    status: VersionSharingRequestStatus


class VersionSharingRequestCreateSchema(BaseSchema):
    """Version Sharing Request schema used for creation."""

    version_id: UUID
    project_code: str
    initiator_username: str
    status: VersionSharingRequestStatus = Field(VersionSharingRequestStatus.SENT, const=True)


class VersionSharingRequestUpdateSchema(BaseSchema):
    """Version Sharing Request schema used for update."""

    status: VersionSharingRequestStatus
    receiver_username: str


class VersionSharingRequestStartSchema(BaseSchema):
    """Version Sharing Request schema used to start the sharing process."""

    job_id: str
    session_id: str


class VersionSharingRequestResponseSchema(VersionSharingRequestSchema):
    """Default schema for single Version Sharing Request in response."""

    id: UUID
    dataset_id: UUID
    dataset_code: str
    source_project_id: UUID
    version_number: str
    created_at: datetime

    class Config:
        orm_mode = True


class VersionSharingRequestListResponseSchema(ListResponseSchema):
    """Default schema for multiple Version Sharing Requests in response."""

    result: list[VersionSharingRequestResponseSchema]
