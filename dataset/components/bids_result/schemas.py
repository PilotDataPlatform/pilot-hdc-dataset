# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from typing import Any
from typing import Dict

from dataset.components.schemas import BaseSchema


class BIDSResultSchema(BaseSchema):
    """General BIDS result schema."""

    dataset_code: str


class BIDSResultResponseSchema(BIDSResultSchema):
    """Default schema for single BIDS result in response."""

    created_time: datetime
    updated_time: datetime
    validate_output: Dict[str, Any]

    class Config:
        orm_mode = True


class LegacyBIDSResultResponseSchema(BaseSchema):
    """Legacy schema for single BIDS result in response."""

    result: BIDSResultResponseSchema


class UpdateBIDSResultSchema(BaseSchema):
    """Schema for create or update the BIDS result."""

    validate_output: Dict[str, Any]
