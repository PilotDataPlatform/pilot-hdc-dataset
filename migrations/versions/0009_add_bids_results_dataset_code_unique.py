# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""add unique key to dataset_code in bids_result.

Revision ID: 0009
Revises: 0008
Create Date: 2023-01-09 18:20:06.699235
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('bids_results_dataset_code_unique', 'bids_results', ['dataset_code'])


def downgrade():
    op.drop_constraint('bids_results_dataset_code_unique', 'bids_results')
