# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest_asyncio
from aiokafka import AIOKafkaConsumer
from testcontainers.kafka import KafkaContainer


@pytest_asyncio.fixture(scope='session')
def kafka_url():
    with KafkaContainer() as kafka_container:
        yield kafka_container.get_bootstrap_server()


@pytest_asyncio.fixture(scope='session')
async def kafka_dataset_consumer(kafka_url):
    consumer = AIOKafkaConsumer('dataset.activity', bootstrap_servers=kafka_url)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest_asyncio.fixture(scope='session')
async def kafka_file_folder_consumer(kafka_url):
    consumer = AIOKafkaConsumer('metadata.items.activity', bootstrap_servers=kafka_url)
    await consumer.start()
    yield consumer
    await consumer.stop()
