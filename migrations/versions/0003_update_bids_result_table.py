# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Update bids_result table.

Revision ID: 0003
Revises: 0002
Create Date: 2022-07-11 11:59:20.714018
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('dataset_geid', 'bids_results', ['dataset_geid'])


def downgrade():
    op.drop_constraint('dataset_geid', 'bids_results')
