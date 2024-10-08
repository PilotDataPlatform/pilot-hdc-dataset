# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import Select

from dataset.components.crud import CRUD
from dataset.components.dataset.models import Dataset
from dataset.components.exceptions import AlreadyExists
from dataset.components.exceptions import NotFound
from dataset.components.version.models import Version


class VersionCRUD(CRUD):
    """CRUD for managing version database models."""

    model = Version

    @property
    def select_query(self) -> Select:
        """Return base select including join with Dataset model."""
        return select(self.model).join(Dataset).options(contains_eager(self.model.dataset))

    async def get_dataset_version_by_version_number(self, dataset_id: UUID, version: str) -> Version:
        """Retrieve version by specific dataset id and version number."""
        statement = select(self.model).where((and_(self.model.version == version, self.model.dataset_id == dataset_id)))
        return await self._retrieve_one(statement)

    async def get_last_dataset_version(self, dataset_id: UUID) -> Version:
        """Retrieve last version from specific dataset."""
        statement = select(self.model).where(self.model.dataset_id == dataset_id).order_by(Version.created_at.desc())
        return await self._retrieve_one(statement)

    async def get_version(self, dataset_id: UUID, version: Optional[str] = None) -> Version:
        """Retrieve specific version from dataset when version otherwise last version from specific dataset."""
        if version:
            return await self.get_dataset_version_by_version_number(dataset_id, version)
        return await self.get_last_dataset_version(dataset_id)

    async def check_duplicate_versions(self, version: str, dataset_id: UUID) -> None:
        """Check if version number already exists to dataset."""
        try:
            await self.get_dataset_version_by_version_number(dataset_id, version)
        except NotFound:
            return
        raise AlreadyExists
