# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""change dataset_geid default from template_schema.

Revision ID: 0004
Revises: 0003
Create Date: 2022-07-13 16:13:22.537504
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('schema_template', 'dataset_geid', nullable=True)


def downgrade():
    op.execute("UPDATE schema_template SET dataset_geid = '' where schema_template.dataset_geid is null")
    op.alter_column('schema_template', 'dataset_geid', nullable=False)
