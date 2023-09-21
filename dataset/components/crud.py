# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import Union
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.engine import Result
from sqlalchemy.engine import ScalarResult
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import Executable
from sqlalchemy.sql import Select

from dataset.components.db_model import DBModel
from dataset.components.exceptions import AlreadyExists
from dataset.components.exceptions import NotFound
from dataset.components.exceptions import ServiceException
from dataset.components.exceptions import UnhandledException
from dataset.components.filtering import Filtering
from dataset.components.pagination import Page
from dataset.components.pagination import Pagination
from dataset.components.schemas import BaseSchema
from dataset.components.sorting import Sorting


class CRUD:
    """Base CRUD class for managing database models."""

    session: AsyncSession
    model: Type[DBModel]
    db_error_codes: dict[str, ServiceException] = {
        '23503': NotFound(),  # missing foreign key
        '23505': AlreadyExists(),  # duplicated entry
    }

    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session
        self.transaction = None

    async def __aenter__(self) -> 'CRUD':
        """Start a new transaction."""

        self.transaction = self.session.begin_nested()
        await self.transaction.__aenter__()

        return self

    async def __aexit__(self, *args: Any) -> None:
        """Commit an existing transaction."""

        await self.transaction.__aexit__(*args)

        return None

    @property
    def select_query(self) -> Select:
        """Create base select."""
        return select(self.model)

    async def execute(self, statement: Executable, **kwds: Any) -> Union[CursorResult, Result]:
        """Execute a statement and return buffered result."""
        try:
            return await self.session.execute(statement, **kwds)
        except Exception as e:
            if isinstance(e, DBAPIError):
                pg_code = e.orig.pgcode
                if pg_code in self.db_error_codes:
                    raise self.db_error_codes.get(pg_code)
            raise UnhandledException()

    async def scalars(self, statement: Executable, **kwds: Any) -> ScalarResult:
        """Execute a statement and return scalar result."""

        return await self.session.scalars(statement, **kwds)

    async def _create_one(self, statement: Executable) -> Union[UUID, str]:
        """Execute a statement to create one entry."""
        result = await self.execute(statement)
        return result.inserted_primary_key.id

    async def _retrieve_one(self, statement: Executable) -> DBModel:
        """Execute a statement to retrieve one entry."""

        result = await self.scalars(statement)
        instance = result.first()

        if instance is None:
            raise NotFound()

        return instance

    async def _retrieve_many(self, statement: Executable) -> List[DBModel]:
        """Execute a statement to retrieve multiple entries."""

        result = await self.scalars(statement)
        instances = result.all()

        return instances

    async def _update_one(self, statement: Executable) -> None:
        """Execute a statement to update one entry."""

        result = await self.execute(statement)

        if result.rowcount == 0:
            raise NotFound()

    async def _delete_one(self, statement: Executable) -> None:
        """Execute a statement to delete one entry."""

        result = await self.execute(statement)

        if result.rowcount == 0:
            raise NotFound()

    async def create(self, entry_create: BaseSchema, **kwds: Any) -> DBModel:
        """Create a new entry."""
        values = entry_create.dict()
        statement = insert(self.model).values(**(values | kwds))
        entry_id = await self._create_one(statement)

        entry = await self.retrieve_by_id(entry_id)

        return entry

    async def retrieve_by_id(self, id_: UUID) -> DBModel:
        """Get an existing entry by id (primary key)."""

        statement = self.select_query.where(self.model.id == id_)
        entry = await self._retrieve_one(statement)

        return entry

    async def paginate(
        self, pagination: Pagination, sorting: Optional[Sorting] = None, filtering: Optional[Filtering] = None
    ) -> Page:
        """Get all existing entries with pagination support."""

        count_statement = select(func.count()).select_from(self.model)
        if filtering:
            count_statement = filtering.apply(count_statement, self.model)
        count = await self._retrieve_one(count_statement)

        entries_statement = self.select_query.limit(pagination.limit).offset(pagination.offset)
        if sorting:
            entries_statement = sorting.apply(entries_statement, self.model)
        if filtering:
            entries_statement = filtering.apply(entries_statement, self.model)
        entries = await self._retrieve_many(entries_statement)

        return Page(pagination=pagination, count=count, entries=entries)

    async def update(self, id_: UUID, entry_update: BaseSchema, **kwds: Any) -> DBModel:
        """Update an existing entry attributes."""

        values = entry_update.dict(exclude_unset=True, exclude_defaults=True)
        statement = update(self.model).where(self.model.id == id_).values(**(values | kwds))
        await self._update_one(statement)

        entry = await self.retrieve_by_id(id_)

        return entry

    async def delete(self, id_: UUID) -> None:
        """Remove an existing entry."""

        statement = delete(self.model).where(self.model.id == id_)

        await self._delete_one(statement)
