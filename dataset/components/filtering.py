# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Type

from pydantic import BaseModel
from sqlalchemy.sql import Select

from dataset.components import DBModel


class Filtering(BaseModel):
    """Base filtering control parameters."""

    def __bool__(self) -> bool:
        """Filtering considered valid when at least one attribute does not have a default value."""

        values = self.dict()

        for name, field in self.__fields__.items():
            if values[name] != field.default:
                return True

        return False

    def apply(self, statement: Select, model: Type[DBModel]) -> Select:
        """Return statement with applied filtering."""

        raise NotImplementedError
