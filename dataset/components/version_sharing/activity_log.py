# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.version_sharing.models import VersionSharingRequest
from dataset.dependencies.kafka import KafkaProducerClient
from dataset.dependencies.kafka import get_kafka_client


class VersionSharingActivityLog(BaseDatasetActivityLog):
    """Class for managing the version sharing event send to the msg broker."""

    async def send_sharing_request_update(self, sharing_request: VersionSharingRequest) -> None:
        """Announce changes in sharing request status."""

        log_schema = DatasetActivityLogSchema(
            activity_type='sharing_request_update',
            version=sharing_request.version_number,
            container_code=sharing_request.dataset_code,
            user=sharing_request.get_username_for_activity_log(),
            changes=sharing_request.get_changes_for_activity_log(),
        )

        return await self._message_send(log_schema.dict())


def get_version_sharing_activity_log(
    kafka_producer_client: KafkaProducerClient = Depends(get_kafka_client),
) -> VersionSharingActivityLog:
    """Return an instance of VersionSharingActivityLog as a dependency."""

    return VersionSharingActivityLog(kafka_producer_client=kafka_producer_client)
