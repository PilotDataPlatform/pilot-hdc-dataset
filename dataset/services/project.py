# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

from dataset.config import get_settings
from dataset.services.base import BaseService

settings = get_settings()


class ProjectService(BaseService):
    BASE_URL = settings.PROJECT_SERVICE

    async def get_by_id(self, id_: str) -> Dict[str, Any]:
        url = f'{self.BASE_URL}/v1/projects/{id_}'
        return await self.get(url)
