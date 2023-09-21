# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema

from .models import Dataset


class DatasetActivityLog(BaseDatasetActivityLog):
    """Class for managing the dataset event send to the msg broker."""

    async def send_dataset_on_create_event(self, dataset: Dataset):
        """Anounce new dataset created."""

        log_schema = DatasetActivityLogSchema(activity_type='create', container_code=dataset.code, user=dataset.creator)

        return await self._message_send(log_schema.dict())
