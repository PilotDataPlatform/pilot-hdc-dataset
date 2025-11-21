# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Add name dataset id unique key to schema template.

Revision ID: 0007
Revises: 58d846d0dfaf
Create Date: 2022-12-07 17:44:10.460344
"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '58d846d0dfaf'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('schema_tpl_geid_fkey', 'schema', type_='foreignkey')
    op.alter_column(
        'schema_template',
        'geid',
        new_column_name='id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='geid::uuid',
    )
    op.alter_column(
        'schema',
        'tpl_geid',
        new_column_name='schema_template_id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='tpl_geid::uuid',
    )
    op.create_foreign_key(
        'schema_schema_template_id_fkey',
        'schema',
        'schema_template',
        ['schema_template_id'],
        ['id'],
        ondelete='cascade',
    )

    op.alter_column(
        'schema_template',
        'dataset_geid',
        new_column_name='dataset_id',
        type_=postgresql.UUID(as_uuid=True),
        postgresql_using='dataset_geid::uuid',
    )
    op.create_unique_constraint('name_dataset_id_unique', 'schema_template', ['name', 'dataset_id'])
    op.create_foreign_key(
        'schema_template_dataset_id_fkey', 'schema_template', 'datasets', ['dataset_id'], ['id'], ondelete='cascade'
    )


def downgrade():
    op.drop_constraint('schema_template_dataset_id_fkey', 'schema_template', type_='foreignkey')
    op.drop_constraint('name_dataset_id_unique', 'schema_template', type_='unique')
    op.alter_column('schema_template', 'dataset_id', new_column_name='dataset_geid', type_=postgresql.VARCHAR())

    op.drop_constraint('schema_schema_template_id_fkey', 'schema', type_='foreignkey')
    op.alter_column('schema_template', 'id', new_column_name='geid', type_=postgresql.VARCHAR())
    op.alter_column('schema', 'schema_template_id', new_column_name='tpl_geid', type_=postgresql.VARCHAR())
    op.create_foreign_key(
        'schema_tpl_geid_fkey', 'schema', 'schema_template', ['tpl_geid'], ['geid'], ondelete='cascade'
    )
