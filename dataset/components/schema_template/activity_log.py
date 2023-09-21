# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.activity_log.dataset_activity_log import BaseDatasetActivityLog
from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.dataset.models import Dataset
from dataset.components.schema_template.models import SchemaTemplate


class SchemaTemplateActivityLogService(BaseDatasetActivityLog):
    """Class for managing the schema template event send to the msg broker."""

    async def send_schema_template_on_create_event(self, schema_template: SchemaTemplate, dataset: Dataset):
        """Anounce new schema templates created."""

        log_schema = DatasetActivityLogSchema(
            activity_type='template_create',
            container_code=dataset.code,
            user=schema_template.creator,
            target_name=schema_template.name,
        )
        return await self._message_send(log_schema.dict())

    async def send_schema_template_on_delete_event(self, schema_template: SchemaTemplate, dataset: Dataset):
        """Anounce schema template deleted."""

        log_schema = DatasetActivityLogSchema(
            activity_type='template_delete',
            container_code=dataset.code,
            user=schema_template.creator,
            target_name=schema_template.name,
        )
        return await self._message_send(log_schema.dict())
