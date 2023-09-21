# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum
from typing import List


class StrEnum(str, Enum):
    """Enum where members suppose to be strings."""

    @property
    def value(self) -> str:
        return self._value_

    @classmethod
    def values(cls) -> List[str]:
        return [field.value for field in cls]
