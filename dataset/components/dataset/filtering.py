# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from typing import Optional
from typing import Tuple
from typing import Type
from uuid import UUID

from sqlalchemy.sql import Select

from dataset.components.filtering import Filtering

from .models import Dataset


class DatasetFiltering(Filtering):
    """Datasets filtering control parameters."""

    code: Optional[str] = None
    creator: Optional[str] = None
    created_at: Optional[Tuple[datetime, datetime]] = None
    ids: Optional[list[UUID]] = None
    codes: Optional[list[str]] = None
    project_id: Optional[UUID] = None

    def apply(self, statement: Select, model: Type[Dataset]) -> Select:
        """Return statement with applied filtering."""

        if self.code:
            statement = statement.where(model.code.ilike(self.code))

        if self.creator:
            statement = statement.where(model.creator.ilike(self.creator))

        if self.created_at:
            statement = statement.where(model.created_at.between(*self.created_at))

        if self.ids:
            statement = statement.where(model.id.in_(self.ids))

        if self.codes:
            statement = statement.where(model.code.in_(self.codes))

        if self.project_id:
            statement = statement.where(model.project_id == self.project_id)

        return statement
