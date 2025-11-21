# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import UUID

from fastapi import Query
from pydantic import validator

from dataset.components.dataset.filtering import DatasetFiltering
from dataset.components.parameters import FilterParameters
from dataset.components.parameters import SortByFields


class DatasetSortByFields(SortByFields):
    """Fields by which datasets can be sorted."""

    CODE = 'code'
    CREATOR = 'creator'
    CREATED_AT = 'created_at'


class DatasetFilterParameters(FilterParameters):
    """Query parameters for datasets filtering."""

    code: str | None = Query(default=None)
    creator: str | None = Query(default=None)
    created_at_start: datetime | None = Query(default=None)
    created_at_end: datetime | None = Query(default=None)
    ids: str | None = Query(default=None)
    code_any: str | None = Query(default=None)
    project_id: UUID | None = Query(default=None)
    project_id_any: str | None = Query(default=None)
    or_creator: str | None = Query(default=None)

    @validator('code_any')
    def list_split_list_parameters(cls, value: str | None) -> list[str] | None:
        if not value:
            return None

        values = [v.strip() for v in value.split(',')]
        if not all(values):
            raise ValueError('invalid value in the comma-separated list')

        return values

    @validator('ids', 'project_id_any')
    def list_split_cast_values_to_uuid(cls, value: str | None) -> list[UUID] | None:
        """Split ids and cast the values from str to UUID."""

        if not value:
            return None

        return [UUID(v) for v in value.split(',')]

    def to_filtering(self) -> DatasetFiltering:
        created_at = None
        if self.created_at_start and self.created_at_end:
            created_at = (self.created_at_start, self.created_at_end)

        return DatasetFiltering(
            creator=self.creator,
            code=self.code,
            created_at=created_at,
            ids=self.ids,
            codes=self.code_any,
            project_id=self.project_id,
            project_ids=self.project_id_any,
            or_creator=self.or_creator,
        )
