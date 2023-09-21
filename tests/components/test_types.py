# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.types import StrEnum


class TestStrEnum:
    def test_values_returns_list_of_enum_values(self):
        class CustomStrEnum(StrEnum):
            KEY1 = 'value1'
            KEY2 = 'value2'

        expected_values = ['value1', 'value2']

        assert CustomStrEnum.values() == expected_values
