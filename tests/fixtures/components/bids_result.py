# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

import pytest

from dataset.components import ModelList
from dataset.components.bids_result.crud import BIDSResultCRUD
from dataset.components.bids_result.models import BIDSResult
from dataset.components.bids_result.schemas import UpdateBIDSResultSchema
from tests.fixtures.components._base_factory import BaseFactory


class BIDSResultFactory(BaseFactory):
    """Create BIDS result related entries for testing purposes."""

    def generate(  # noqa: C901
        self,
        validate_output: Dict[str, Any] = ...,
    ) -> UpdateBIDSResultSchema:
        if validate_output is ...:
            validate_output = self.fake.pydict(value_types=[str, int, bool])

        return UpdateBIDSResultSchema(
            validate_output=validate_output,
        )

    async def create(
        self,
        validate_output: Dict[str, Any] = ...,
        **kwds: Any,
    ) -> BIDSResult:
        entry = self.generate(validate_output)
        async with self.crud:
            return await self.crud.create(entry, **kwds)

    async def bulk_create(
        self,
        number: int,
        validate_output: Dict[str, Any] = ...,
        **kwds: Any,
    ):
        return ModelList(
            [
                await self.create(
                    validate_output,
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def bids_result_crud(db_session) -> BIDSResultCRUD:
    yield BIDSResultCRUD(db_session)


@pytest.fixture
def bids_result_factory(faker, bids_result_crud) -> BIDSResultFactory:
    yield BIDSResultFactory(faker, bids_result_crud)
