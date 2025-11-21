# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.filtering import Filtering


class TestFiltering:
    def test__bool__returns_true_when_at_least_one_attribute_is_set(self):
        class CustomFiltering(Filtering):
            field: list[str] | None = None

        filtering = CustomFiltering(field=['value'])

        assert bool(filtering) is True

    def test__bool__returns_false_when_all_attributes_are_not_set(self):
        class CustomFiltering(Filtering):
            field: int | None = None

        filtering = CustomFiltering()

        assert bool(filtering) is False
