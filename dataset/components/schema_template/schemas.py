# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import Field

from dataset.components.schemas import BaseSchema


class SchemaTemplateSchema(BaseSchema):
    """General schema template schema."""

    name: str
    is_draft: bool
    content: Dict[str, Any]


class SchemaTemplateCreateSchema(SchemaTemplateSchema):
    """Schema for create schema template."""

    standard: str
    system_defined: bool
    creator: str
    dataset_id: Optional[UUID] = None


class SchemaTemplateResponse(SchemaTemplateSchema):
    """General schema for schema template response."""

    id: UUID = Field(alias='geid')
    standard: str
    system_defined: bool
    creator: str
    dataset_id: Optional[UUID] = None
    create_timestamp: datetime
    update_timestamp: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class LegacySchemaTemplateResponse(BaseSchema):
    """Legacy schema for single schema template in response."""

    result: SchemaTemplateResponse


class LegacySchemaTemplateItemListResponse(BaseSchema):
    """Legacy schema for multiple schema template in response."""

    id: UUID = Field(alias='geid')
    name: str
    system_defined: bool
    standard: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class LegacySchemaTemplateListResponse(BaseSchema):
    """Legacy schema for multiple schema templates in response."""

    result: List[LegacySchemaTemplateItemListResponse]
