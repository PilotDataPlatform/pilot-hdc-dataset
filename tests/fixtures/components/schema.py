# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

import pytest

from dataset.components.dataset.models import Dataset
from dataset.components.models import ModelList
from dataset.components.schema.crud import SchemaCRUD
from dataset.components.schema.models import SchemaDataset
from dataset.components.schema.schemas import POSTSchema
from tests.fixtures.components._base_factory import BaseFactory


class SchemaFactory(BaseFactory):
    """Create schema related entries for testing purposes."""

    def generate(
        self,
        name: str = ...,
        dataset_id: str = ...,
        schema_template_id: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: dict = ...,
        creator: str = ...,
    ) -> POSTSchema:
        if name is ...:
            name = self.fake.word()

        if creator is ...:
            creator = self.fake.unique.first_name()

        if standard is ...:
            standard = self.fake.sentence()

        if system_defined is ...:
            system_defined = False

        if is_draft is ...:
            is_draft = False

        if content is ...:
            content = {}

        if dataset_id is ...:
            dataset_id = self.fake.uuid4(cast_to=str)

        if schema_template_id is ...:
            schema_template_id = self.fake.uuid4(cast_to=str)

        return POSTSchema(
            name=name,
            dataset_id=dataset_id,
            schema_template_id=schema_template_id,
            standard=standard,
            system_defined=system_defined,
            is_draft=is_draft,
            content=content,
            creator=creator,
        )

    async def create(
        self,
        name: str = ...,
        dataset_id: str = ...,
        schema_template_id: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: dict = ...,
        creator: str = ...,
        **kwds: Any,
    ) -> SchemaDataset:
        entry = self.generate(
            name, dataset_id, schema_template_id, standard, system_defined, is_draft, content, creator
        )
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def create_essentials(self, dataset: Dataset) -> SchemaDataset:
        async with self.crud:
            return await self.crud.create_essentials(dataset)

    async def bulk_create(
        self,
        number: int,
        name: str = ...,
        dataset_id: str = ...,
        schema_template_id: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: dict = ...,
        creator: str = ...,
        **kwds: Any,
    ):
        return ModelList(
            [
                await self.create(
                    name,
                    creator,
                    standard,
                    system_defined,
                    is_draft,
                    content,
                    dataset_id,
                    schema_template_id,
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def schema_crud(db_session) -> SchemaCRUD:
    yield SchemaCRUD(db_session)


@pytest.fixture
def schema_factory(faker, schema_crud) -> SchemaFactory:
    yield SchemaFactory(faker, schema_crud)
