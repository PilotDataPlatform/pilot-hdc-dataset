# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from dataset.components.schemas import BaseSchema


def get_current_datetime():
    return datetime.now(timezone.utc)


class ActivityDetailsSchema(BaseSchema):
    name: str
    targets: List[str]


class ActivitySchema(BaseSchema):
    action: str
    resource: str
    detail: ActivityDetailsSchema

    def get_changes(self) -> List[Dict[str, Any]]:
        return [{'property': target.lower() for target in self.detail.targets}]


class BaseActivityLogSchema(BaseModel):
    activity_time: datetime = Field(default_factory=get_current_datetime)
    changes: List[Dict[str, Any]] = []
    activity_type: str
    user: str
    container_code: str


class DatasetActivityLogSchema(BaseActivityLogSchema):
    version: Optional[str]
    target_name: Optional[str] = None


class FileFolderActivityLogSchema(BaseActivityLogSchema):
    item_id: UUID
    item_type: str
    item_name: str
    item_parent_path: str = ''
    container_type: str = 'dataset'
    zone: int = 1
    imported_from: Optional[str] = None
