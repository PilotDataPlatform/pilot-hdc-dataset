# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""0006: Update bids validate column.

Revision ID: 58d846d0dfaf
Revises: 0005
Create Date: 2022-08-17 10:50:03.786057
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '58d846d0dfaf'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('bids_results', 'dataset_geid', new_column_name='dataset_code')
    op.execute(
        'UPDATE bids_results \
        SET dataset_code = datasets.code \
            FROM datasets \
                WHERE datasets.id::text like bids_results.dataset_code;'
    )


def downgrade():
    op.execute(
        'UPDATE bids_results \
               SET dataset_code=datasets.id \
               FROM datasets \
               WHERE datasets.code=bids_results.dataset_code'
    )
    op.alter_column('bids_results', 'dataset_code', new_column_name='dataset_geid')
