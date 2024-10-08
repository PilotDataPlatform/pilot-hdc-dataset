# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.dependencies.db import get_db_session
from dataset.dependencies.kafka import get_kafka_client
from dataset.dependencies.s3 import get_s3_client

__all__ = ['get_s3_client', 'get_db_session', 'get_kafka_client']
