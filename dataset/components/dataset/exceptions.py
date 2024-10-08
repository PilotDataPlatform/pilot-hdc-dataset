# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.exceptions import AlreadyExists
from dataset.components.exceptions import NotFound


class DatasetNotFound(NotFound):
    """Raised when required dataset is not found."""

    domain: str = 'dataset'

    @property
    def details(self) -> str:
        return 'Dataset is not found'


class DatasetCodeConflict(AlreadyExists):
    """Raised when required dataset with dataset_code already exists."""

    domain: str = 'dataset'

    @property
    def details(self) -> str:
        return 'Dataset with this code already exists.'
