# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime

from pydantic import BaseModel
from pydantic import constr

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.schemas import BaseSchema

FOLDER_NAME_REGEX = r'^[^\\\/:?\*<>|"]+$'


class StorageSchema(BaseSchema):
    """Base storage schema."""

    location_uri: str | None = None


class FolderResponseSchema(BaseSchema):
    """Base folder schema."""

    id: str
    parent: str | None = None
    parent_path: str | None = None
    status: ItemStatusSchema
    type: str
    name: str
    size: int
    owner: str
    container_code: str
    container_type: str
    created_time: datetime
    last_updated_time: datetime
    storage: StorageSchema | None = None


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
    """Schema to create metadata folder."""

    parent: str | None = None
    parent_path: str | None = None
    type: str = 'folder'
    name: str
    owner: str
    status: ItemStatusSchema = ItemStatusSchema.ACTIVE
    container_code: str
    container_type: str = 'dataset'


class FileMetadataCreateSchema(FolderMetadataCreateSchema):
    """Schema to create metadata file."""

    location_uri: str | None = None
    size: int = 0
