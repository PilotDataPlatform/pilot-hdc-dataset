# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dataset.components.schema.crud import SchemaCRUD
from dataset.dependencies import get_db_session


def get_schema_crud(db_session: AsyncSession = Depends(get_db_session)) -> SchemaCRUD:
    """Return an instance of SchemaCRUD as a dependency."""

    return SchemaCRUD(db_session)
