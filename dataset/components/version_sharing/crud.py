# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import Select

from dataset.components.crud import CRUD
from dataset.components.dataset import Dataset
from dataset.components.version import Version
from dataset.components.version_sharing import VersionSharingRequest
from dataset.dependencies import get_db_session


class VersionSharingRequestCRUD(CRUD):
    """CRUD for managing Version Sharing Request models."""

    model = VersionSharingRequest

    @property
    def select_query(self) -> Select:
        """Return base select including join with Version and Dataset models."""

        return (
            select(self.model)
            .join(Version)
            .join(Dataset)
            .options(contains_eager(self.model.version).contains_eager(Version.dataset))
        )


def get_version_sharing_request_crud(
    db_session: Annotated[AsyncSession, Depends(get_db_session)]
) -> VersionSharingRequestCRUD:
    """Return an instance of VersionSharingRequestCRUD as a dependency."""

    return VersionSharingRequestCRUD(db_session)
