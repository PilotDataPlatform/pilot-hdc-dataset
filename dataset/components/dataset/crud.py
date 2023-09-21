# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Union
from uuid import UUID

from sqlalchemy.future import select

from dataset.components.crud import CRUD
from dataset.components.dataset.exceptions import DatasetNotFound
from dataset.components.dataset.models import Dataset
from dataset.components.exceptions import NotFound


class DatasetCRUD(CRUD):
    """CRUD for managing dataset database models."""

    model = Dataset

    async def retrieve_by_code(self, code: str) -> Dataset:
        """Get an existing dataset by unique code."""

        statement = select(self.model).where(self.model.code == code)
        try:
            dataset = await self._retrieve_one(statement)
        except NotFound:
            raise DatasetNotFound()

        return dataset

    async def retrieve_by_id(self, id_: UUID) -> Dataset:
        """Get an existing dataset by unique code."""
        try:
            return await super().retrieve_by_id(id_)
        except NotFound:
            raise DatasetNotFound()

    async def retrieve_by_id_or_code(self, id_or_code: Union[UUID, str]) -> Dataset:
        """Get an existing dataset either by id or by code (depending on type)."""
        if isinstance(id_or_code, UUID):
            dataset = await self.retrieve_by_id(id_or_code)
        else:
            dataset = await self.retrieve_by_code(id_or_code)
        return dataset
