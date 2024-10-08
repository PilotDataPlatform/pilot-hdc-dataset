# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""legacy tables.

Revision ID: 0001
Revises:
Create Date: 2022-05-06 11:54:58.190003
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'bids_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_geid', sa.String(), nullable=True),
        sa.Column('created_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('validate_output', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schema_template',
        sa.Column('geid', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('dataset_geid', sa.String(), nullable=True),
        sa.Column('standard', sa.String(), nullable=True),
        sa.Column('system_defined', sa.Boolean(), nullable=True),
        sa.Column('is_draft', sa.Boolean(), nullable=True),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('create_timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('update_timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('creator', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('geid'),
    )
    op.create_table(
        'version',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_code', sa.String(), nullable=True),
        sa.Column('dataset_geid', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'schema',
        sa.Column('geid', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('dataset_geid', sa.String(), nullable=True),
        sa.Column('tpl_geid', sa.String(), nullable=True),
        sa.Column('standard', sa.String(), nullable=True),
        sa.Column('system_defined', sa.Boolean(), nullable=True),
        sa.Column('is_draft', sa.Boolean(), nullable=True),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('create_timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('update_timestamp', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('creator', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ['tpl_geid'],
            ['schema_template.geid'],
        ),
        sa.PrimaryKeyConstraint('geid'),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schema')
    op.drop_table('version')
    op.drop_table('schema_template')
    op.drop_table('bids_results')
    # ### end Alembic commands ###
