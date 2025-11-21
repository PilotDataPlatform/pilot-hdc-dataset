# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Change version primary key to uuid.

Revision ID: 0014
Revises: 0013
Create Date: 2025-02-11 10:46:05.672046
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = '0013'


def upgrade():
    op.drop_column('version', 'id')

    context = op.get_context()
    context.connection.execute(sa.text('DROP SEQUENCE IF EXISTS version_id_seq'))

    op.add_column(
        'version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
    )
    op.alter_column('version', 'id', server_default=None)
    op.create_primary_key('version_pkey', 'version', ['id'])


def downgrade():
    op.drop_column('version', 'id')

    context = op.get_context()
    context.connection.execute(sa.text('CREATE SEQUENCE IF NOT EXISTS version_id_seq START WITH 1'))

    op.add_column(
        'version', sa.Column('id', sa.Integer(), nullable=False, server_default=sa.text("nextval('version_id_seq')"))
    )
    op.create_primary_key('version_pkey', 'version', ['id'])
