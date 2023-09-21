# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Optional
from typing import Type
from uuid import UUID

from sqlalchemy.sql import Select

from dataset.components.filtering import Filtering
from dataset.components.version.models import Version


class VersionFiltering(Filtering):
    """Version filtering control parameters."""

    dataset_id: Optional[UUID] = None

    def apply(self, statement: Select, model: Type[Version]) -> Select:
        """Return statement with applied filtering."""

        if self.dataset_id:
            statement = statement.where(model.dataset_id == self.dataset_id)

        return statement
