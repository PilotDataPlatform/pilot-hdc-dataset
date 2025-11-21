# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Query

from dataset.components.parameters import FilterParameters
from dataset.components.parameters import SortByFields
from dataset.components.version_sharing.filtering import VersionSharingRequestFiltering


class VersionSharingRequestSortByFields(SortByFields):
    """Fields by which Version Sharing Requests can be sorted."""

    CREATED_AT = 'created_at'


class VersionSharingRequestFilterParameters(FilterParameters):
    """Query parameters for Version Sharing Requests filtering."""

    project_code: str | None = Query(default=None)

    def to_filtering(self) -> VersionSharingRequestFiltering:
        return VersionSharingRequestFiltering(
            project_code=self.project_code,
        )
