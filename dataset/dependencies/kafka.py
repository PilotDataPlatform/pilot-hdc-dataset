# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import asyncio

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from fastapi import Depends

from dataset.config import Settings
from dataset.config import get_settings
from dataset.logger import logger


class KafkaProducerClient:

    def __init__(self, producer: AIOKafkaProducer) -> None:
        self.producer = producer

    async def send(self, topic: str, msg: bytes) -> None:
        try:
            await self.producer.send(topic, msg)
            logger.info(f'Message sent to Kafka topic "{topic}"')
        except KafkaError:
            logger.exception(f'Error sending message to Kafka topic "{topic}"')
            raise


class GetKafkaClient:
    """Class to create KafkaProducerClient connection instance."""

    def __init__(self) -> None:
        self.instance = None
        self.lock = asyncio.Lock()

    async def __call__(self, settings: Settings = Depends(get_settings)) -> KafkaProducerClient:
        """Return an instance of KafkaProducerClient class."""

        async with self.lock:
            if not self.instance:
                producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_URL)
                await producer.start()
                self.instance = producer
            return self.instance


get_kafka_client = GetKafkaClient()
