# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.sql import Select

from dataset.components.db_model import DBModel
from dataset.components.types import StrEnum


class SortingOrder(StrEnum):
    """Available sorting orders."""

    ASC = 'asc'
    DESC = 'desc'


class Sorting(BaseModel):
    """Base sorting control parameters."""

    field: str | None = None
    order: SortingOrder

    def __bool__(self) -> bool:
        """Sorting considered valid when the field is specified."""

        return self.field is not None

    def apply(self, statement: Select, model: type[DBModel]) -> Select:
        """Return statement with applied ordering."""

        field = getattr(model, self.field)

        order_by = asc(field)
        if self.order is SortingOrder.DESC:
            order_by = desc(field)

        return statement.order_by(order_by)
