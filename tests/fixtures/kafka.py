# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import AsyncIterator
from collections.abc import Iterator

import pytest
from aiokafka import AIOKafkaConsumer
from aiokafka import AIOKafkaProducer
from testcontainers.kafka import KafkaContainer

from dataset.dependencies.kafka import KafkaProducerClient


@pytest.fixture(scope='session')
def kafka_url() -> Iterator[str]:
    with KafkaContainer() as kafka_container:
        yield kafka_container.get_bootstrap_server()


@pytest.fixture(scope='session')
async def kafka_producer_client(kafka_url) -> AsyncIterator[KafkaProducerClient]:
    producer = AIOKafkaProducer(bootstrap_servers=kafka_url)
    await producer.start()
    yield KafkaProducerClient(producer)
    await producer.stop()


@pytest.fixture
async def kafka_dataset_consumer(kafka_url) -> AsyncIterator[AIOKafkaConsumer]:
    consumer = AIOKafkaConsumer('dataset.activity', bootstrap_servers=kafka_url)
    await consumer.start()
    yield consumer
    await consumer.stop()


@pytest.fixture
async def kafka_file_folder_consumer(kafka_url) -> AsyncIterator[AIOKafkaConsumer]:
    consumer = AIOKafkaConsumer('metadata.items.activity', bootstrap_servers=kafka_url)
    await consumer.start()
    yield consumer
    await consumer.stop()
