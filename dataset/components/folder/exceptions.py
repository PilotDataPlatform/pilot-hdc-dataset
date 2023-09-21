# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.exceptions import NotFound


class FolderNotFound(NotFound):
    """Raised when required folder is not found."""

    domain: str = 'folder'

    @property
    def details(self) -> str:
        return 'Folder is not found'
