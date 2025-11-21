# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import UUID

from pydantic import constr

from dataset.components.schemas import BaseSchema
from dataset.components.schemas import ListResponseSchema
from dataset.config import get_settings

settings = get_settings()


class VersionCreateSchema(BaseSchema):
    """Schema for create version."""

    operator: str
    notes: constr(max_length=250)
    version: constr(regex=settings.DATASET_VERSION_NUMBER_REGEX, strip_whitespace=True)


class VersionSchema(BaseSchema):
    """General schema version."""

    dataset_id: UUID
    dataset_code: str
    location: str
    created_by: str
    notes: str
    version: str


class VersionResponseSchema(VersionSchema):
    """General schema for single version response."""

    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True


class VersionListResponseSchema(ListResponseSchema):
    """Legacy schema for multiple versions in response."""

    result: list[VersionResponseSchema]
