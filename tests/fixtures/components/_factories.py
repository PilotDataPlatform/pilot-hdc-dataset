# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy import text

from dataset.components.crud import CRUD
from tests.fixtures.fake import Faker


class FakeFactory:
    fake: Faker

    def __init__(self, fake: Faker) -> None:
        self.fake = fake


class CRUDFactory(FakeFactory):
    crud: CRUD

    def __init__(self, crud: CRUD, fake: Faker) -> None:
        super().__init__(fake)

        self.crud = crud

    async def truncate_table(self) -> None:
        """Remove all rows from a table."""

        statement = text(f'TRUNCATE TABLE {self.crud.model.__table__} CASCADE')
        await self.crud.execute(statement)
        await self.crud.commit()
