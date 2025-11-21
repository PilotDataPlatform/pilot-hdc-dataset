# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Add indices on created_at and creator in dataset.

Revision ID: 0012
Revises: 0011
Create Date: 2023-02-15 23:15:45.846082
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = '0011'


def upgrade():
    op.create_index('ix_dataset_datasets_created_at', 'datasets', ['created_at'], unique=False)
    op.create_index('ix_dataset_datasets_creator', 'datasets', ['creator'], unique=False)
    op.create_index('ix_datasets_dataset_created_at_creator', 'datasets', ['created_at', 'creator'], unique=False)


def downgrade():
    op.drop_index('ix_dataset_datasets_created_at', table_name='datasets')
    op.drop_index('ix_dataset_datasets_creator', table_name='datasets')
    op.drop_index('ix_datasets_dataset_created_at_creator', table_name='datasets')
