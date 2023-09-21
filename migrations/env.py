# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from logging.config import fileConfig
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from dataset.components.models import DBModel
from dataset.config import get_settings

settings = get_settings()
logger = logging.getLogger('alembic')
config = context.config
fileConfig(config.config_file_name)

target_metadata = DBModel.metadata
database_uri = config.get_main_option('database_uri', settings.OPS_DB_URI)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = database_uri.replace(f'{urlparse(database_uri).scheme}://', 'postgresql://', 1)
    connectable = create_engine(url, poolclass=NullPool, echo=settings.RDS_ECHO_SQL_QUERIES)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    logger.error('Offline migrations environment is not supported.')
    exit(1)

run_migrations_online()
