# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from dataset.config import get_settings
from dataset.logger import logger

settings = get_settings()


class GetDBEngine:
    """Create a FastAPI callable dependency for SQLAlchemy single AsyncEngine instance."""

    def __init__(self) -> None:
        self.instance = None

    async def __call__(self) -> AsyncEngine:
        """Return an instance of AsyncEngine class."""

        if not self.instance:
            try:
                self.instance = create_async_engine(
                    settings.OPS_DB_URI, echo=settings.RDS_ECHO_SQL_QUERIES, pool_pre_ping=settings.RDS_PRE_PING
                )
            except SQLAlchemyError:
                logger.exception('Error DB connect')
        return self.instance


db_engine = GetDBEngine()


async def get_db_session(engine: AsyncEngine = Depends(db_engine)) -> AsyncSession:
    db = AsyncSession(bind=engine, expire_on_commit=False)
    try:
        yield db
        await db.commit()
    finally:
        await db.close()
