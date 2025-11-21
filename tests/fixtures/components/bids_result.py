# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import AsyncGenerator
from typing import Any

import pytest

from dataset.components import ModelList
from dataset.components.bids_result.crud import BIDSResultCRUD
from dataset.components.bids_result.models import BIDSResult
from dataset.components.bids_result.schemas import UpdateBIDSResultSchema
from tests.fixtures.components import CRUDFactory


class BIDSResultFactory(CRUDFactory):
    """Create BIDS result related entries for testing purposes."""

    def generate(  # noqa: C901
        self,
        validate_output: dict[str, Any] = ...,
    ) -> UpdateBIDSResultSchema:
        if validate_output is ...:
            validate_output = self.fake.pydict(value_types=[str, int, bool])

        return UpdateBIDSResultSchema(
            validate_output=validate_output,
        )

    async def create(
        self,
        validate_output: dict[str, Any] = ...,
        **kwds: Any,
    ) -> BIDSResult:
        entry = self.generate(validate_output)

        return await self.crud.create(entry, **kwds)

    async def bulk_create(
        self,
        number: int,
        validate_output: dict[str, Any] = ...,
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
    return BIDSResultCRUD(db_session)


@pytest.fixture
async def bids_result_factory(fake, bids_result_crud) -> AsyncGenerator[BIDSResultFactory]:
    bids_result_factory = BIDSResultFactory(bids_result_crud, fake)
    yield bids_result_factory
    await bids_result_factory.truncate_table()
