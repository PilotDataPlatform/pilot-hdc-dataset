# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from functools import lru_cache
from typing import Any

from common import VaultClient
from pydantic import BaseSettings
from pydantic import Extra
from pydantic import Field
from starlette.config import Config

config = Config('.env')
SRV_NAMESPACE = config('APP_NAME', cast=str, default='service_dataset')
CONFIG_CENTER_ENABLED = config('CONFIG_CENTER_ENABLED', cast=str, default='false')
CONFIG_CENTER_BASE_URL = config('CONFIG_CENTER_BASE_URL', cast=str, default='NOT_SET')


def load_vault_settings(settings: BaseSettings) -> dict[str, Any]:
    if CONFIG_CENTER_ENABLED == 'false':
        return {}
    else:
        vc = VaultClient(config('VAULT_URL'), config('VAULT_CRT'), config('VAULT_TOKEN'))
        return vc.get_from_vault(SRV_NAMESPACE)


class Settings(BaseSettings):
    DEBUG: bool = False
    PORT: int = 5081
    HOST: str = '0.0.0.0'
    RELOAD: bool = True
    env: str = ''
    WORKERS: int = 4

    LOGGING_LEVEL: int = logging.INFO
    LOGGING_FORMAT: str = 'json'

    DATASET_FILE_FOLDER: str = 'data'

    DATASET_CODE_REGEX: str = r'^[a-z0-9]{3,32}$'
    DATASET_VERSION_NUMBER_REGEX: str = r'^\d+\.\d+$'

    # disk mounts
    ROOT_PATH: str

    S3_INTERNAL: str = 'minio.minio:9000'
    S3_INTERNAL_HTTPS: bool = False
    S3_PUBLIC: str = 'public'
    S3_PUBLIC_HTTPS: bool = True
    S3_HOST: str = '127.0.0.1'
    S3_PORT: int = 9100
    S3_HTTPS_ENABLED: bool = False
    S3_GATEWAY_ENABLED: bool = False
    S3_ACCESS_KEY: str = Field('ACCESSKEY/GMIMPKTWGOKHIQYYQHPO', env={'S3_ACCESS_KEY', 'MINIO_ACCESS_KEY'})
    S3_SECRET_KEY: str = Field('SECRETKEY/HJGKVAS/TRglfFvzDrbYpdknbc', env={'S3_SECRET_KEY', 'MINIO_SECRET_KEY'})
    S3_BUCKET_ENCRYPTION_ENABLED: bool = False

    # External services
    QUEUE_SERVICE: str
    DATA_OPS_UTIL: str
    METADATA_SERVICE: str
    PROJECT_SERVICE: str

    # Postgres
    OPSDB_UTILITY_HOST: str = '127.0.0.1'
    OPSDB_UTILITY_PORT: str = '5432'
    OPSDB_UTILITY_USERNAME: str = 'postgres'
    OPSDB_UTILITY_PASSWORD: str = 'postgres'
    RDS_ECHO_SQL_QUERIES: bool = False
    RDS_DBNAME: str = 'dataset'
    RDS_PRE_PING: bool = True

    # Redis Service
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ''

    KAFKA_URL: str = ''

    MAX_PREVIEW_SIZE: int = 500000

    # dataset schema default
    ESSENTIALS_NAME: str = 'essential.schema.json'
    ESSENTIALS_TEMPLATE_NAME: str = 'Essential'

    OPEN_TELEMETRY_ENABLED: bool = False
    OPEN_TELEMETRY_HOST: str = '127.0.0.1'
    OPEN_TELEMETRY_PORT: int = 6831

    ENABLE_PROMETHEUS_METRICS: bool = False

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return init_settings, env_settings, load_vault_settings, file_secret_settings

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

        self.MINIO_TMP_PATH = self.ROOT_PATH + '/tmp/'

        self.QUEUE_SERVICE += '/v1'
        self.DATA_UTILITY_SERVICE_V1 = self.DATA_OPS_UTIL + '/v1'
        self.DATA_UTILITY_SERVICE_v2 = self.DATA_OPS_UTIL + '/v2'

        self.OPS_DB_URI = (
            f'postgresql+asyncpg://{self.OPSDB_UTILITY_USERNAME}:{self.OPSDB_UTILITY_PASSWORD}'
            f'@{self.OPSDB_UTILITY_HOST}:{self.OPSDB_UTILITY_PORT}/{self.RDS_DBNAME}'
        )

        s3_protocol = 'https' if self.S3_HTTPS_ENABLED else 'http'
        self.S3_ENDPOINT_URL = f'{s3_protocol}://{self.S3_HOST}:{self.S3_PORT}'


@lru_cache(1)
def get_settings() -> Settings:
    settings = Settings()
    return settings
