# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.sql import Select

from dataset.components.dataset.models import Dataset
from dataset.components.filtering import Filtering


class DatasetFiltering(Filtering):
    """Datasets filtering control parameters."""

    code: str | None = None
    creator: str | None = None
    created_at: tuple[datetime, datetime] | None = None
    ids: list[UUID] | None = None
    codes: list[str] | None = None
    project_id: UUID | None = None
    project_ids: list[UUID] | None = None
    or_creator: str | None = None

    def apply(self, statement: Select, model: type[Dataset]) -> Select:
        """Return statement with applied filtering."""

        and_clauses = []
        or_clauses = []

        if self.code:
            and_clauses.append(model.code.ilike(self.code))

        if self.creator:
            and_clauses.append(model.creator.ilike(self.creator))

        if self.created_at:
            and_clauses.append(model.created_at.between(*self.created_at))

        if self.ids:
            and_clauses.append(model.id.in_(self.ids))

        if self.codes:
            and_clauses.append(model.code.in_(self.codes))

        if self.project_id:
            and_clauses.append(model.project_id == self.project_id)

        if self.project_ids:
            and_clauses.append(model.project_id.in_(self.project_ids))

        if self.or_creator:
            or_clauses.append(model.creator.ilike(self.or_creator))

        statement = statement.where(or_(and_(*and_clauses), *or_clauses))

        return statement
