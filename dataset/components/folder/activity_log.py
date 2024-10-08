# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from uuid import UUID

from dataset.components.activity_log.file_folder_activity_log import BaseFileFolderActivityLog
from dataset.components.activity_log.schemas import FileFolderActivityLogSchema
from dataset.components.folder.schemas import FolderResponseSchema


class FolderActivityLog(BaseFileFolderActivityLog):
    """Class for managing the folder event send to the msg broker."""

    async def send_create_folder_event(self, folder: FolderResponseSchema, user: str) -> Dict[str, Any]:
        """send folder created msg to msg broker."""

        log_schema = FileFolderActivityLogSchema(
            container_code=folder.container_code,
            user=user,
            activity_type='create',
            item_id=UUID(folder.id),
            item_type=folder.type,
            item_name=folder.name,
        )
        await self._message_send(log_schema.dict())
