# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.version.crud import VersionCRUD
from dataset.components.version.models import Version
from dataset.components.version.schemas import VersionSchema
from tests.fixtures.components._base_factory import BaseFactory


class VersionFactory(BaseFactory):
    """Create version related entries for testing purposes."""

    def generate(  # noqa: C901
        self,
        notes: str = ...,
        created_by: str = ...,
        version: str = ...,
        dataset_code: str = ...,
        dataset_id: UUID = ...,
        location: str = ...,
    ) -> VersionSchema:
        if notes is ...:
            notes = self.fake.sentence()

        if notes is ...:
            notes = self.fake.word()

        if created_by is ...:
            created_by = self.fake.unique.first_name()

        if version is ...:
            version = self.fake.numerify('%!.%!')

        if dataset_code is ...:
            dataset_code = self.fake.word()

        if dataset_id is ...:
            dataset_id = dataset_id = self.fake.uuid4(cast_to=None)

        if location is ...:
            location = f'minio://http://{self.fake.ipv4()}/{dataset_code}/version.zip'

        return VersionSchema(
            notes=notes,
            created_by=created_by,
            version=version,
            dataset_code=dataset_code,
            dataset_id=dataset_id,
            location=location,
        )

    async def create(
        self,
        notes: str = ...,
        created_by: str = ...,
        version: str = ...,
        dataset_code: str = ...,
        dataset_id: UUID = ...,
        location: str = ...,
        **kwds: Any,
    ) -> Version:
        entry = self.generate(notes, created_by, version, dataset_code, dataset_id, location)
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def bulk_create(
        self,
        number: int,
        notes: str = ...,
        created_by: str = ...,
        version: str = ...,
        dataset_code: str = ...,
        dataset_id: UUID = ...,
        location: str = ...,
        **kwds: Any,
    ):
        return ModelList(
            [
                await self.create(
                    notes,
                    created_by,
                    version,
                    dataset_code,
                    dataset_id,
                    location,
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def version_crud(db_session) -> VersionCRUD:
    yield VersionCRUD(db_session)


@pytest.fixture
def version_factory(faker, version_crud) -> VersionFactory:
    yield VersionFactory(faker, version_crud)
