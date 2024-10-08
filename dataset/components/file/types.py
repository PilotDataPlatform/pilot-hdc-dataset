# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from enum import Enum

from pydantic import BaseModel


class EFileStatus(Enum):
    """Base class for file status."""

    WAITING = 0
    RUNNING = 1
    SUCCEED = 2
    FAILED = 3
    CHUNK_UPLOADED = 4


class EActionType(Enum):
    """Base class for action type."""

    data_upload = 0
    data_download = 1
    data_transfer = 2
    data_delete = 3
    data_import = 4
    data_rename = 5
    data_validate = 6


class FileStatus(BaseModel):
    session_id: str
    target_names: list[str]
    target_type: str
    container_code: str
    container_type: str
    action_type: str
    status: str
    job_id: str
