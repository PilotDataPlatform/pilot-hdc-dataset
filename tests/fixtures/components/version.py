# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.crud import CRUD
from dataset.components.version.crud import VersionCRUD
from dataset.components.version.models import Version
from dataset.components.version.schemas import VersionSchema
from tests.fixtures.components import CRUDFactory
from tests.fixtures.components.dataset import DatasetFactory
from tests.fixtures.fake import Faker


class VersionFactory(CRUDFactory):
    """Create version related entries for testing purposes."""

    def __init__(self, crud: CRUD, fake: Faker, dataset_factory: DatasetFactory) -> None:
        super().__init__(crud, fake)

        self.dataset_factory = dataset_factory

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
            dataset_id = self.fake.uuid4(cast_to=None)

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

        return await self.crud.create(entry, **kwds)

    async def create_with_dataset(
        self,
        notes: str = ...,
        created_by: str = ...,
        version: str = ...,
        location: str = ...,
        **kwds: Any,
    ) -> Version:
        dataset = await self.dataset_factory.create()

        return await self.create(notes, created_by, version, dataset.code, dataset.id, location, **kwds)

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
    return VersionCRUD(db_session)


@pytest.fixture
async def version_factory(fake, version_crud, dataset_factory) -> AsyncGenerator[VersionFactory]:
    version_factory = VersionFactory(version_crud, fake, dataset_factory)
    yield version_factory
    await version_factory.truncate_table()
