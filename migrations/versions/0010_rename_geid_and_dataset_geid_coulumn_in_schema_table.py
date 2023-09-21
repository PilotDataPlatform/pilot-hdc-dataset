# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""rename geid and dataset geid coulumn in schema table.

Revision ID: 0010
Revises: 0009
Create Date: 2023-01-17 12:35:54.367730
"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = '0009'


def upgrade():
    op.alter_column(
        'schema',
        'geid',
        new_column_name='id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='geid::uuid',
    )
    op.alter_column(
        'schema',
        'dataset_geid',
        new_column_name='dataset_id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='dataset_geid::uuid',
    )
    op.create_foreign_key('schema_dataset_id_fkey', 'schema', 'datasets', ['dataset_id'], ['id'], ondelete='cascade')


def downgrade():
    op.drop_constraint('schema_dataset_id_fkey', 'schema', type_='foreignkey')
    op.alter_column('schema', 'dataset_id', new_column_name='dataset_geid', type_=postgresql.VARCHAR())
    op.alter_column('schema', 'id', new_column_name='geid', type_=postgresql.VARCHAR())
