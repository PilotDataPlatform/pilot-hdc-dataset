# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import constr

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.schemas import BaseSchema

FOLDER_NAME_REGEX = r'^[^\\\/:?\*<>|"]+$'


class StorageSchema(BaseSchema):
    """Base storage schema."""

    location_uri: Optional[str] = None


class FolderResponseSchema(BaseSchema):
    """Base folder schema."""

    id: str
    parent: Optional[str] = None
    parent_path: Optional[str] = None
    status: ItemStatusSchema
    type: str
    name: str
    size: int
    owner: str
    container_code: str
    container_type: str
    created_time: datetime
    last_updated_time: datetime
    storage: Optional[StorageSchema] = None


class FolderCreateSchema(BaseModel):
    """Base schema to create folder."""

    folder_name: constr(regex=FOLDER_NAME_REGEX, max_length=20, strip_whitespace=True)
    username: str
    parent_folder_geid: str = ''
    status: ItemStatusSchema = ItemStatusSchema.ACTIVE


class LegacyFolderResponseSchema(BaseSchema):
    """Legacy schema for single BIDS result in response."""

    result: FolderResponseSchema


class FolderMetadataCreateSchema(BaseSchema):
    """schema to create metadata folder."""

    parent: Optional[str] = None
    parent_path: Optional[str] = None
    type: str = 'folder'
    name: str
    owner: str
    status: ItemStatusSchema = ItemStatusSchema.ACTIVE
    container_code: str
    container_type: str = 'dataset'


class FileMetadataCreateSchema(FolderMetadataCreateSchema):
    """schema to create metadata file."""

    location_uri: Optional[str] = None
    size: int = 0
