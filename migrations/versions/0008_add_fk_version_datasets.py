# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""add relation between versions table and datasets table.

Revision ID: 0008
Revises: 0007
Create Date: 2022-12-01 11:43:59.693367
"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'version',
        'dataset_geid',
        new_column_name='dataset_id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='dataset_geid::uuid',
        nullable=False,
    )
    op.create_foreign_key(
        'version_dataset_id_fkey',
        'version',
        'datasets',
        ['dataset_id'],
        ['id'],
        ondelete='cascade',
    )
    op.create_unique_constraint('dataset_id_version_unique', 'version', ['dataset_id', 'version'])


def downgrade():
    op.drop_constraint('dataset_id_version_unique', 'version', type_='unique')
    op.drop_constraint('version_dataset_id_fkey', 'version', type_='foreignkey')
    op.alter_column('version', 'dataset_id', new_column_name='dataset_geid', type_=postgresql.VARCHAR(), nullable=True)
