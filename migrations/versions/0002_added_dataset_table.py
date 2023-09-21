# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""Added dataset table.

Revision ID: 0002
Revises: 0001
Create Date: 2022-05-10 10:49:41.878977
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.VARCHAR(length=256), nullable=False),
        sa.Column('authors', postgresql.ARRAY(sa.VARCHAR(length=256)), nullable=False),
        sa.Column('code', sa.VARCHAR(length=32), nullable=False),
        sa.Column('type', sa.VARCHAR(length=256), nullable=False),
        sa.Column('modality', postgresql.ARRAY(sa.VARCHAR(length=256)), nullable=True),
        sa.Column('collection_method', postgresql.ARRAY(sa.VARCHAR(length=256)), nullable=True),
        sa.Column('license', sa.VARCHAR(length=256), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.VARCHAR(length=256)), nullable=True),
        sa.Column('description', sa.VARCHAR(length=5000), nullable=False),
        sa.Column('size', sa.INTEGER(), nullable=True),
        sa.Column('total_files', sa.INTEGER(), nullable=True),
        sa.Column('title', sa.VARCHAR(length=256), nullable=False),
        sa.Column('creator', sa.VARCHAR(length=256), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dataset_datasets_code'), 'datasets', ['code'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_dataset_datasets_code'), table_name='datasets')
    op.drop_table('datasets')
    # ### end Alembic commands ###
