# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.schema_template.crud import SchemaTemplateCRUD
from dataset.components.schema_template.models import SchemaTemplate
from dataset.components.schema_template.schemas import SchemaTemplateCreateSchema
from tests.fixtures.components._base_factory import BaseFactory


class SchemaTemplateFactory(BaseFactory):
    """Create schema template related entries for testing purposes."""

    def generate(
        self,
        name: str = ...,
        creator: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: Dict[str, Any] = ...,
        dataset_id: UUID = ...,
    ) -> SchemaTemplateCreateSchema:
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
            dataset_id = self.fake.uuid4(cast_to=None)

        return SchemaTemplateCreateSchema(
            name=name,
            creator=creator,
            standard=standard,
            system_defined=system_defined,
            is_draft=is_draft,
            content=content,
            dataset_id=dataset_id,
        )

    async def create(
        self,
        name: str = ...,
        creator: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: Dict[str, Any] = ...,
        dataset_id: UUID = ...,
        **kwds: Any,
    ) -> SchemaTemplate:
        entry = self.generate(name, creator, standard, system_defined, is_draft, content, dataset_id)
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def bulk_create(
        self,
        number: int,
        name: str = ...,
        creator: str = ...,
        standard: str = ...,
        system_defined: bool = ...,
        is_draft: bool = ...,
        content: Dict[str, Any] = ...,
        dataset_id: UUID = ...,
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
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def schema_template_crud(db_session) -> SchemaTemplateCRUD:
    yield SchemaTemplateCRUD(db_session)


@pytest.fixture
def schema_template_factory(faker, schema_template_crud) -> SchemaTemplateFactory:
    yield SchemaTemplateFactory(faker, schema_template_crud)
