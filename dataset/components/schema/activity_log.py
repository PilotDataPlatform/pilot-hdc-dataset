# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import ActivitySchema
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.schema.models import SchemaDataset
from dataset.dependencies.kafka import KafkaProducerClient
from dataset.dependencies.kafka import get_kafka_client


class SchemaDatasetActivityLogService(BaseDatasetActivityLog):
    """Class for managing the schema event send to the msg broker."""

    async def send_schema_create_event(self, schema: SchemaDataset, username: str):
        """Anounce new schema created."""

        log_schema = DatasetActivityLogSchema(
            activity_type='schema_create', container_code=schema.dataset.code, user=username, target_name=schema.name
        )
        return await self._message_send(log_schema.dict())

    async def send_schema_update_event(self, schema: SchemaDataset, username: str, changes: list[ActivitySchema]):
        """Anounce schema updated."""

        log_schema = DatasetActivityLogSchema(
            activity_type='schema_update',
            container_code=schema.dataset.code,
            user=username,
            target_name=schema.name,
            changes=changes[0].get_changes() if changes else [],
        )
        return await self._message_send(log_schema.dict())

    async def send_schema_delete_event(self, schema: SchemaDataset, username: str):
        """Anounce new schema deleted."""

        log_schema = DatasetActivityLogSchema(
            activity_type='schema_delete',
            container_code=schema.dataset.code,
            user=username,
            target_name=schema.name,
        )
        return await self._message_send(log_schema.dict())


def get_schema_dataset_activity_log_service(
    kafka_producer_client: KafkaProducerClient = Depends(get_kafka_client),
) -> SchemaDatasetActivityLogService:
    """Return an instance of SchemaDatasetActivityLogService as a dependency."""

    return SchemaDatasetActivityLogService(kafka_producer_client=kafka_producer_client)
