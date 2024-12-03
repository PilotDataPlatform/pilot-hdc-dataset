# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from aiokafka.errors import KafkaConnectionError
from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from dataset.dependencies import get_db_session
from dataset.dependencies.kafka import get_kafka_client
from dataset.logger import logger


async def is_kafka_connected() -> bool:
    try:
        await get_kafka_client()
        return True
    except KafkaConnectionError:
        logger.exception('Kafka connection error')
        return False


async def is_db_connected(db: AsyncSession = Depends(get_db_session)) -> bool:
    """Validates DB connection."""

    try:
        connection = await db.connection()
        raw_connection = await connection.get_raw_connection()
        if not raw_connection.is_valid:
            return False
    except SQLAlchemyError:
        logger.exception('DB connection failed, SQLAlchemyError')
        return False
    except Exception:
        logger.exception('DB connection failed, unknown Exception')
        return False
    return True
