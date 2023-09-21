# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from time import time
from typing import Any
from typing import Dict

from dataset.config import get_settings
from dataset.logger import logger
from dataset.services.base import BaseService

settings = get_settings()


class QueueService(BaseService):
    BASE_URL = settings.QUEUE_SERVICE
    HEADERS = {'Content-type': 'application/json; charset=utf-8'}

    async def send_message(self, dataset_code: str) -> Dict[str, Any]:
        payload = {
            'event_type': 'bids_validate',
            'payload': {
                'dataset_code': str(dataset_code),
                'project': 'dataset',
                'access_token': self._get_authorization_token(),
            },
            'create_timestamp': time(),
        }
        url = self.BASE_URL + '/send_message'
        logger.info(f'Sending Message To Queue: {payload}')
        response = await self.create(url=url, payload=payload)
        return response
