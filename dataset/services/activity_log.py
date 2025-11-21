# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io
from typing import Any

from fastavro import schema
from fastavro import schemaless_writer

from dataset.dependencies.kafka import KafkaProducerClient
from dataset.logger import logger


class ActivityLogService:

    def __init__(self, *, kafka_producer_client: KafkaProducerClient) -> None:
        self.kafka_producer_client = kafka_producer_client

    async def _message_send(self, data: dict[str, Any] = None) -> None:
        logger.info(f'Sending socket notification: {str(data)}')
        loaded_schema = schema.load_schema(self.avro_schema_path)
        bio = io.BytesIO()
        try:
            schemaless_writer(bio, loaded_schema, data)
            msg = bio.getvalue()
        except ValueError:
            logger.exception('Error during the AVRO validation.')
            raise

        await self.kafka_producer_client.send(self.topic, msg)
        logger.info('Socket notification successfully sent')
