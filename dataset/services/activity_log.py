# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io
from typing import Any
from typing import Dict

from fastavro import schema
from fastavro import schemaless_writer

from dataset.dependencies import get_kafka_client
from dataset.logger import logger


class ActivityLogService:
    async def _message_send(self, data: Dict[str, Any] = None) -> dict:
        logger.info(f'Sending socket notification: {str(data)}')
        loaded_schema = schema.load_schema(self.avro_schema_path)
        bio = io.BytesIO()
        try:
            schemaless_writer(bio, loaded_schema, data)
            msg = bio.getvalue()
        except ValueError:
            logger.exception('Error during the AVRO validation.')
            raise
        client = await get_kafka_client()
        await client.send(self.topic, msg)
