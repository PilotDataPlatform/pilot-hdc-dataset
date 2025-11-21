# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from dataset.components.schemas import BaseSchema


def get_current_datetime():
    return datetime.now(timezone.utc)


class ActivityDetailsSchema(BaseSchema):
    name: str
    targets: list[str]


class ActivitySchema(BaseSchema):
    action: str
    resource: str
    detail: ActivityDetailsSchema

    def get_changes(self) -> list[dict[str, Any]]:
        return [{'property': target.lower() for target in self.detail.targets}]


class BaseActivityLogSchema(BaseModel):
    activity_time: datetime = Field(default_factory=get_current_datetime)
    changes: list[dict[str, Any]] = []
    network_origin: str = 'unknown'
    activity_type: str
    user: str
    container_code: str


class DatasetActivityLogSchema(BaseActivityLogSchema):
    version: str | None
    target_name: str | None = None


class FileFolderActivityLogSchema(BaseActivityLogSchema):
    item_id: UUID
    item_type: str
    item_name: str
    item_parent_path: str = ''
    container_type: str = 'dataset'
    zone: int = 1
    imported_from: str | None = None
