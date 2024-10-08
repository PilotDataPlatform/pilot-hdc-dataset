# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dataset.components.db_model import DBModel


class ModelList(list):
    """Store a list of models of the same type."""

    def _get_nested_field(self, source: DBModel, field: str) -> Any:
        """Return field value for any level of field in model."""
        try:
            relationship, relationship_field = field.split('.', 1)
            source = getattr(source, relationship)
            return self._get_nested_field(source, relationship_field)
        except ValueError:
            return getattr(source, field)

    def map_by_field(self, field: str, key_type: Optional[type] = None) -> Dict[Any, Any]:
        """Create map using field argument as key with optional type casting."""

        results = {}
        for source in self:
            key = self._get_nested_field(source, field)

            if key_type is not None:
                key = key_type(key)

            results[key] = source

        return results

    def get_field_values(self, field: str) -> List[Any]:
        """Return list with values each model has in field attribute."""
        field_values_list = []
        for source in self:
            field_values_list.append(self._get_nested_field(source, field))
        return field_values_list
