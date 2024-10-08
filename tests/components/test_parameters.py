# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import inspect

from dataset.components.pagination import Pagination
from dataset.components.parameters import PageParameters
from dataset.components.parameters import SortByFields
from dataset.components.parameters import SortParameters


class TestPageParameters:
    def test_to_pagination_returns_instance_of_pagination_with_the_same_page_arguments(self, faker):
        page = faker.pyint()
        page_size = faker.pyint()
        page_parameters = PageParameters(page=page, page_size=page_size)

        pagination = page_parameters.to_pagination()

        assert isinstance(pagination, Pagination)
        assert pagination.page == page
        assert pagination.page_size == page_size


class TestSortParameters:
    def test_with_sort_by_fields_returns_a_class_with_overridden_type_annotation_for_sort_by_field(self):
        class CustomSortByFields(SortByFields):
            field = 'field'

        sort_parameters_class = SortParameters.with_sort_by_fields(CustomSortByFields)

        signature = inspect.signature(sort_parameters_class)
        sort_by_field = signature.parameters['sort_by']

        assert sort_by_field.annotation is CustomSortByFields

    def test_with_sort_by_fields_does_not_override_original_class_type_annotation_for_sort_by_field(self):
        class CustomSortByFields(SortByFields):
            field = 'field'

        SortParameters.with_sort_by_fields(CustomSortByFields)

        signature = inspect.signature(SortParameters)
        sort_by_field = signature.parameters['sort_by']

        assert sort_by_field.annotation is str
