# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import List
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.dataset.crud import DatasetCRUD
from dataset.components.dataset.models import Dataset
from dataset.components.dataset.schemas import DatasetSchema
from dataset.components.dataset.schemas import DatasetType
from dataset.components.dataset.schemas import Modality
from tests.fixtures.components._base_factory import BaseFactory


class DatasetFactory(BaseFactory):
    """Create dataset related entries for testing purposes."""

    def generate(  # noqa: C901
        self,
        code: str = ...,
        creator: str = ...,
        title: str = ...,
        authors: List[str] = ...,
        modality: List[str] = ...,
        collection_method: List[str] = ...,
        tags: List[str] = ...,
        description: str = ...,
        type_: str = ...,
        license_: str = ...,
    ) -> DatasetSchema:
        if code is ...:
            code = self.fake.pystr_format('?#' * 10).lower()

        if title is ...:
            title = self.fake.word()

        if creator is ...:
            creator = self.fake.unique.first_name()

        if authors is ...:
            authors = [self.fake.unique.first_name()]

        if description is ...:
            description = self.fake.sentence()

        if modality is ...:
            modality = [self.fake.random_element(Modality).value]

        if tags is ...:
            tags = self.fake.words(3, unique=True)

        if collection_method is ...:
            collection_method = self.fake.words(3, unique=True)

        if type_ is ...:
            type_ = self.fake.random_element(DatasetType).value

        if license_ is ...:
            license_ = self.fake.word()

        return DatasetSchema(
            creator=creator,
            title=title,
            code=code,
            authors=authors,
            type=type_,
            modality=modality,
            collection_method=collection_method,
            license=license_,
            tags=tags,
            description=description,
        )

    async def create(
        self,
        creator: str = ...,
        title: str = ...,
        code: str = ...,
        authors: List[str] = ...,
        type_: str = ...,
        modality: List[str] = ...,
        collection_method: List[str] = ...,
        license_: str = ...,
        tags: List[str] = ...,
        description: str = ...,
        **kwds: Any,
    ) -> Dataset:
        entry = self.generate(
            creator, title, code, authors, type_, modality, collection_method, license_, tags, description
        )
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def create_with_project(
        self,
        creator: str = ...,
        title: str = ...,
        code: str = ...,
        authors: List[str] = ...,
        type_: str = ...,
        modality: List[str] = ...,
        collection_method: List[str] = ...,
        license_: str = ...,
        tags: List[str] = ...,
        description: str = ...,
        project_id: UUID = ...,
        **kwds: Any,
    ):
        if project_id is ...:
            project_id = self.fake.uuid4(cast_to=None)

        return await self.create(
            creator,
            title,
            code,
            authors,
            type_,
            modality,
            collection_method,
            license_,
            tags,
            description,
            project_id=project_id,
            **kwds,
        )

    async def bulk_create(
        self,
        number: int,
        creator: str = ...,
        title: str = ...,
        code: str = ...,
        authors: List[str] = ...,
        type_: str = ...,
        modality: List[str] = ...,
        collection_method: List[str] = ...,
        license_: str = ...,
        tags: List[str] = ...,
        description: str = ...,
        **kwds: Any,
    ):
        return ModelList(
            [
                await self.create(
                    creator,
                    title,
                    code,
                    authors,
                    type_,
                    modality,
                    collection_method,
                    license_,
                    tags,
                    description,
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def dataset_crud(db_session) -> DatasetCRUD:
    yield DatasetCRUD(db_session)


@pytest.fixture
def dataset_factory(faker, dataset_crud) -> DatasetFactory:
    yield DatasetFactory(faker, dataset_crud)
