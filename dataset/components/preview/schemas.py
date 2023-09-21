# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.schemas import BaseSchema


class PreviewResponseSchema(BaseSchema):
    """Base schema to dataset preview."""

    type: str
    is_concatenated: bool
    content: str


class LegacyPreviewResultResponseSchema(BaseSchema):
    """Legacy schema for single preview result in response."""

    result: PreviewResponseSchema
