# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.version.models import Version
from dataset.dependencies.kafka import KafkaProducerClient
from dataset.dependencies.kafka import get_kafka_client


class VersionActivityLog(BaseDatasetActivityLog):
    """Class for managing the version event send to the msg broker."""

    async def send_publish_version_succeed(self, version: Version):
        """Announce a new version created."""

        log_schema = DatasetActivityLogSchema(
            activity_type='release',
            version=version.version,
            container_code=version.dataset.code,
            user=version.created_by,
        )

        return await self._message_send(log_schema.dict())

    async def send_version_download_event(self, version: Version, operator: str, network_origin: str = 'unknown'):
        """Announce that a version has been downloaded."""

        log_schema = DatasetActivityLogSchema(
            activity_type='download',
            version=version.version,
            container_code=version.dataset.code,
            user=operator,
            target_name=version.filename,
            network_origin=network_origin,
        )

        return await self._message_send(log_schema.dict())


def get_version_activity_log(
    kafka_producer_client: KafkaProducerClient = Depends(get_kafka_client),
) -> VersionActivityLog:
    """Return an instance of VersionActivityLog as a dependency."""

    return VersionActivityLog(kafka_producer_client=kafka_producer_client)
