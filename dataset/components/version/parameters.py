# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Optional
from uuid import UUID

from fastapi import Query

from dataset.components.parameters import FilterParameters
from dataset.components.parameters import SortByFields
from dataset.components.version.filtering import VersionFiltering


class VersionSortByFields(SortByFields):
    """Fields by which versions can be sorted."""

    CREATED_AT = 'created_at'


class VersionFilterParameters(FilterParameters):
    """Query parameters for versions filtering."""

    dataset_id: Optional[UUID] = Query(default=None)

    def to_filtering(self) -> VersionFiltering:
        return VersionFiltering(
            dataset_id=self.dataset_id,
        )
