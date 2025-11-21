# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy.sql import Select

from dataset.components.filtering import Filtering
from dataset.components.version_sharing.models import VersionSharingRequest


class VersionSharingRequestFiltering(Filtering):
    """Version Sharing Request filtering control parameters."""

    project_code: str | None = None

    def apply(self, statement: Select, model: type[VersionSharingRequest]) -> Select:
        """Return statement with applied filtering."""

        if self.project_code:
            statement = statement.where(model.project_code == self.project_code)

        return statement
