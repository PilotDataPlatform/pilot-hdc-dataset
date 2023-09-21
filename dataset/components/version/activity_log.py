# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.version.models import Version


class VersionActivityLog(BaseDatasetActivityLog):
    """Class for managing the version event send to the msg broker."""

    async def send_publish_version_succeed(self, version: Version):
        """Anounce new version created."""

        log_schema = DatasetActivityLogSchema(
            activity_type='release',
            version=version.version,
            container_code=version.dataset.code,
            user=version.created_by,
        )

        return await self._message_send(log_schema.dict())
