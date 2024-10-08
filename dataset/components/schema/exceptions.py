# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.exceptions import NotFound


class SchemaNotFound(NotFound):
    """Raised when required dataset or schema template or schema itself not found."""

    domain: str = 'schema'

    @property
    def details(self) -> str:
        return 'Dataset or Schema Template or Schema not found.'
