# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import List
from typing import Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import Select

from dataset.components.crud import CRUD
from dataset.components.dataset.models import Dataset
from dataset.components.schema_template.models import SchemaTemplate


class SchemaTemplateCRUD(CRUD):
    """CRUD for managing schema template database models."""

    model = SchemaTemplate

    @property
    def select_query(self) -> Select:
        """Return base select including join with Dataset model."""
        return select(self.model).outerjoin(Dataset).options(contains_eager(self.model.dataset))

    async def get_template_by_dataset_or_system_defined(self, dataset_id: Union[UUID, str]) -> List[SchemaTemplate]:
        if isinstance(dataset_id, UUID):
            statement = select(self.model).where(self.model.dataset_id == dataset_id)
        else:
            statement = select(self.model).where(SchemaTemplate.system_defined.is_(True))
        return await self._retrieve_many(statement)

    async def get_template_by_name(self, name: str) -> SchemaTemplate:
        """Retrive schema template by name."""

        statement = select(self.model).where(self.model.name == name)
        return await self._retrieve_one(statement)
