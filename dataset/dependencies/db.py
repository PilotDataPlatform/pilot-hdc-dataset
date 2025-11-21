# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import AsyncGenerator
from uuid import uuid4

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from dataset.config import Settings
from dataset.config import get_settings
from dataset.logger import logger


class GetDBEngine:
    """Create a FastAPI callable dependency for SQLAlchemy single AsyncEngine instance."""

    def __init__(self) -> None:
        self.instance = None

    async def __call__(self, settings: Settings = Depends(get_settings)) -> AsyncEngine:
        """Return an instance of AsyncEngine class."""

        if not self.instance:
            try:
                self.instance = create_async_engine(
                    settings.OPS_DB_URI, echo=settings.RDS_ECHO_SQL_QUERIES, pool_pre_ping=settings.RDS_PRE_PING
                )
            except SQLAlchemyError:
                logger.exception('Error DB connect')
        return self.instance


get_db_engine = GetDBEngine()


async def get_db_session(engine: AsyncEngine = Depends(get_db_engine)) -> AsyncGenerator[AsyncSession]:
    session_id = uuid4()
    session = AsyncSession(bind=engine, expire_on_commit=False, info={'session_id': session_id})
    try:
        logger.info(f'Session "{session_id}" created')
        yield session
        await session.commit()
        logger.info(f'Session "{session_id}" committed')
    except SQLAlchemyError:
        logger.exception(f'Session "{session_id}" failed to commit')
        raise
    finally:
        await session.close()
