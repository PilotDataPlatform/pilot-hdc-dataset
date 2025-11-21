# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Add name dataset_id unique to schema model.

Revision ID: 0011
Revises: 0010
Create Date: 2023-01-18 12:00:42.936753
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = '0010'


def upgrade():
    op.create_unique_constraint('schema_name_dataset_id_unique', 'schema', ['name', 'dataset_id'])


def downgrade():
    op.drop_constraint('schema_name_dataset_id_unique', 'schema', type_='unique')
