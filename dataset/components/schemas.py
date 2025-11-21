# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from dataset.components.pagination import Page


class BaseSchema(BaseModel):
    """Base class for all available schemas."""

    def to_payload(self) -> dict[str, str]:
        return json.loads(self.json(by_alias=True))

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S'),
        }


class ListResponseSchema(BaseSchema):
    """Default schema for multiple base schemas in response."""

    num_of_pages: int
    page: int
    total: int
    result: list[BaseSchema]

    @classmethod
    def from_page(cls, page: Page):
        return cls(num_of_pages=page.total_pages, page=page.number, total=page.count, result=page.entries)


class LegacyResponseSchema(BaseSchema):
    """Legacy schema to keep old response body and avoid to break other services."""

    result: dict[str, Any]
