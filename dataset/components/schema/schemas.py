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

from dataset.components.activity_log.schemas import ActivitySchema
from dataset.components.schemas import BaseSchema


class POSTSchema(BaseSchema):
    """Schema for POST request."""

    name: str
    dataset_id: str = Field(alias='dataset_geid')
    schema_template_id: str = Field(alias='tpl_geid')
    standard: str
    system_defined: bool
    is_draft: bool
    content: dict
    creator: str

    class Config:
        allow_population_by_field_name = True


class POSTSchemaList(BaseSchema):
    """Schema for POST List request."""

    name: Optional[str] = None
    dataset_id: Optional[str] = Field(alias='dataset_geid', default=None)
    schema_template_id: Optional[str] = Field(alias='tpl_geid', default=None)
    standard: Optional[str] = None
    system_defined: Optional[bool] = None
    is_draft: Optional[bool] = None
    create_timestamp: Optional[float] = None
    update_timestamp: Optional[float] = None
    creator: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class PUTSchema(POSTSchema):
    """Schema for PUT request."""

    name: str = None
    dataset_id: str = Field(alias='dataset_geid', default=None)
    schema_template_id: str = Field(alias='tpl_geid', default=None)
    standard: str = None
    system_defined: bool = None
    is_draft: bool = None
    content: dict = None
    creator: str = None
    activity: List[ActivitySchema]
    username: str

    class Config:
        allow_population_by_field_name = True


class DELETESchema(BaseSchema):
    """Schema for DELETE request."""

    dataset_id: str = Field(alias='dataset_geid')
    username: str
    activity: List[ActivitySchema]

    class Config:
        allow_population_by_field_name = True


class UpdateSchema(BaseSchema):
    """Schema for update SchemaDatase model."""

    name: Optional[str] = None
    dataset_id: Optional[str] = None
    schema_template_id: Optional[str] = None
    standard: Optional[str] = None
    system_defined: Optional[bool] = None
    is_draft: Optional[bool] = None
    content: Optional[Dict[str, Any]] = None
    creator: Optional[str] = None


class SchemaResponse(BaseSchema):
    """General schema for schema response."""

    id: UUID = Field(alias='geid')
    name: str
    dataset_id: UUID = Field(alias='dataset_geid')
    schema_template_id: UUID = Field(alias='tpl_geid')
    standard: str
    system_defined: bool
    is_draft: bool
    creator: str
    content: dict
    create_timestamp: datetime
    update_timestamp: datetime

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class LegacySchemaResponse(BaseSchema):
    """Legacy schema for single schema in response."""

    result: Optional[SchemaResponse] = None


class LegacySchemaListResponse(BaseSchema):
    """Legacy schema for multiple schemas in response."""

    result: Optional[List[SchemaResponse]] = None
