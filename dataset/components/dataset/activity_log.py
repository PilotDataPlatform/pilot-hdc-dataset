# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.dataset.models import Dataset
from dataset.dependencies.kafka import KafkaProducerClient
from dataset.dependencies.kafka import get_kafka_client


class DatasetActivityLog(BaseDatasetActivityLog):
    """Class for managing the dataset event send to the msg broker."""

    async def send_dataset_on_create_event(self, dataset: Dataset):
        """Anounce new dataset created."""

        log_schema = DatasetActivityLogSchema(activity_type='create', container_code=dataset.code, user=dataset.creator)

        return await self._message_send(log_schema.dict())


def get_dataset_activity_log(
    kafka_producer_client: KafkaProducerClient = Depends(get_kafka_client),
) -> DatasetActivityLog:
    """Return an instance of DatasetActivityLog as a dependency."""

    return DatasetActivityLog(kafka_producer_client=kafka_producer_client)
