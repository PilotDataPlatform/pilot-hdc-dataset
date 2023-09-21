# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum
from typing import Any
from typing import Dict
from typing import List

from aiobotocore.response import StreamingBody

from dataset.components.schemas import BaseSchema


class FileSchema(BaseSchema):
    """Schema for file."""

    content: str
    type: str
    size: int


class FileStreamSchema(FileSchema):
    """Schema for file stream."""

    content: StreamingBody

    class Config:
        arbitrary_types_allowed = True


class ImportDataPost(BaseSchema):
    """the post request payload for import data from project."""

    source_list: list
    operator: str
    project_geid: str


class DatasetFileDelete(BaseSchema):
    """the delete request payload for dataset to delete files."""

    source_list: list
    operator: str


class DatasetFileMove(BaseSchema):
    """the post request payload for dataset to move files under the dataset."""

    source_list: list
    operator: str
    target_geid: str


class DatasetFileRename(BaseSchema):
    """the post request payload for dataset to move files under the dataset."""

    new_name: str
    operator: str


class FileOperationResponse(BaseSchema):
    """Schema for file operation response."""

    processing: List[Dict[str, Any]]
    ignored: List[Dict[str, Any]]


class LegacyFileResponse(BaseSchema):
    """Legacy schema for single file response."""

    result: FileOperationResponse


class LegacyFileListResponse(BaseSchema):
    """Legacy schema for single file response."""

    total: int
    result: Dict[str, Any]


class ResourceLockingSchema(BaseSchema):
    """Schema for resource locking and unlocking by operation."""

    resource_key: str
    operation: str


class ItemStatusSchema(str, Enum):
    """Schema for item file status."""

    REGISTERED = 'REGISTERED'
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

    def __str__(self) -> str:
        return str(self.name)
