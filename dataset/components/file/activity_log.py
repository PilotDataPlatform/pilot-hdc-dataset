# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import List
from uuid import UUID

from dataset.components.activity_log.file_folder_activity_log import BaseFileFolderActivityLog
from dataset.components.activity_log.schemas import FileFolderActivityLogSchema


class FileActivityLogService(BaseFileFolderActivityLog):
    """Class for managing the file event send to the msg broker."""

    async def send_on_import_event(self, dataset_code: str, project_code: str, imported_list: List[str], user: str):
        """send file imported msg to msg broker."""

        for item in imported_list:
            log_schema = FileFolderActivityLogSchema(
                container_code=dataset_code,
                user=user,
                activity_type='import',
                item_id=UUID(item['id']),
                item_type=item['type'],
                item_name=item['name'],
                imported_from=project_code,
            )
            await self._message_send(log_schema.dict())

    async def send_on_delete_event(self, dataset_code: str, source_list: List[str], user: str):
        """send file delete msg to msg broker."""

        for item in source_list:
            log_schema = FileFolderActivityLogSchema(
                container_code=dataset_code,
                user=user,
                activity_type='delete',
                item_parent_path=item['parent_path'] or '',
                item_id=UUID(item['id']),
                item_type=item['type'],
                item_name=item['name'],
            )
            await self._message_send(log_schema.dict())

    async def send_on_move_event(
        self, dataset_code: str, item: Dict[str, Any], user: str, old_path: str, new_path: str
    ):
        """send file move msg to msg broker."""

        # even thought the event is UPDATE there is no update in metadata service.
        # as of today, when one item is moved, the item is deleted and a new one is created in the new path.
        log_schema = FileFolderActivityLogSchema(
            container_code=dataset_code,
            user=user,
            activity_type='update',
            item_parent_path=item['parent_path'] or '',
            item_id=UUID(item['id']),
            item_type=item['type'],
            item_name=item['name'],
            changes=[{'item_property': 'parent_path', 'old_value': old_path, 'new_value': new_path}],
        )
        await self._message_send(log_schema.dict())

    async def send_on_rename_event(self, dataset_code: str, source_list: List[str], user: str, new_name: str):
        """send file rename msg to msg broker."""

        # even thought the event is UPDATE there is no update in metadata service.
        # as of today, when one item is moved, the item is deleted and a new one is created in the new name.
        for item in source_list:
            log_schema = FileFolderActivityLogSchema(
                container_code=dataset_code,
                user=user,
                activity_type='update',
                item_parent_path=item['parent_path'] or '',
                item_id=UUID(item['id']),
                item_type=item['type'],
                item_name=item['name'],
                changes=[{'item_property': 'name', 'old_value': item['name'], 'new_value': new_name}],
            )
            await self._message_send(log_schema.dict())
