# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum


class StrEnum(str, Enum):
    """Enum where members suppose to be strings."""

    def __str__(self) -> str:
        return self.value

    @property
    def value(self) -> str:
        return self._value_

    @classmethod
    def values(cls) -> list[str]:
        return [field.value for field in cls]
