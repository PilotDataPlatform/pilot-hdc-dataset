# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
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
        *,
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

        if creator is ...:
            creator = self.fake.unique.user_name()

        if title is ...:
            title = self.fake.word()

        if authors is ...:
            authors = [self.fake.unique.first_name()]

        if modality is ...:
            modality = [self.fake.random_element(Modality).value]

        if collection_method is ...:
            collection_method = self.fake.words(3, unique=True)

        if tags is ...:
            tags = self.fake.words(3, unique=True)

        if description is ...:
            description = self.fake.sentence()

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
        *,
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
        **kwds: Any,
    ) -> Dataset:
        entry = self.generate(
            code=code,
            creator=creator,
            title=title,
            authors=authors,
            modality=modality,
            collection_method=collection_method,
            tags=tags,
            description=description,
            type_=type_,
            license_=license_,
        )
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def create_with_project(
        self,
        *,
        project_id: UUID = ...,
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
        **kwds: Any,
    ) -> Dataset:
        if project_id is ...:
            project_id = self.fake.uuid4(cast_to=None)

        return await self.create(
            code=code,
            creator=creator,
            title=title,
            authors=authors,
            modality=modality,
            collection_method=collection_method,
            tags=tags,
            description=description,
            type_=type_,
            license_=license_,
            project_id=project_id,
            **kwds,
        )

    async def bulk_create(
        self,
        number: int,
        *,
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
        **kwds: Any,
    ) -> ModelList[Dataset]:
        return ModelList(
            [
                await self.create(
                    code=code,
                    creator=creator,
                    title=title,
                    authors=authors,
                    modality=modality,
                    collection_method=collection_method,
                    tags=tags,
                    description=description,
                    type_=type_,
                    license_=license_,
                    **kwds,
                )
                for _ in range(number)
            ]
        )

    async def bulk_create_with_project(
        self,
        number: int,
        *,
        project_id: UUID = ...,
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
        **kwds: Any,
    ) -> ModelList[Dataset]:
        return ModelList(
            [
                await self.create_with_project(
                    project_id=project_id,
                    code=code,
                    creator=creator,
                    title=title,
                    authors=authors,
                    modality=modality,
                    collection_method=collection_method,
                    tags=tags,
                    description=description,
                    type_=type_,
                    license_=license_,
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
