# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from faker import Faker

from dataset.components.crud import CRUD


class BaseFactory:
    """Base class for creating testing purpose entries."""

    fake: Faker
    crud: CRUD

    def __init__(self, fake: Faker, crud: CRUD) -> None:
        self.fake = fake
        self.crud = crud
