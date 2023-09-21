# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.sorting import Sorting
from dataset.components.sorting import SortingOrder


class TestSorting:
    def test__bool__returns_true_when_field_attribute_is_set(self):
        sorting = Sorting(field='value', order=SortingOrder.ASC)

        assert bool(sorting) is True

    def test__bool__returns_false_when_field_attribute_is_not_set(self):
        sorting = Sorting(order=SortingOrder.DESC)

        assert bool(sorting) is False
