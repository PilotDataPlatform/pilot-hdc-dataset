# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from typing import List

from pydantic import BaseModel
from pydantic import conint

from dataset.components import DBModel


class Pagination(BaseModel):
    """Base pagination control parameters."""

    page: conint(ge=0) = 0
    page_size: conint(ge=1) = 20

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def offset(self) -> int:
        return self.page_size * self.page


class Page(BaseModel):
    """Represent one page of the response."""

    pagination: Pagination
    count: int
    entries: List[DBModel]

    class Config:
        arbitrary_types_allowed = True

    @property
    def number(self) -> int:
        return self.pagination.page

    @property
    def total_pages(self) -> int:
        return math.ceil(self.count / self.pagination.page_size)
