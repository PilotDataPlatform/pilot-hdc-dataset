# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Add Version Sharing Requests table.

Revision ID: 0015
Revises: 0014
Create Date: 2025-02-13 15:36:59.781925
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = '0014'

version_sharing_request_status = postgresql.ENUM(
    'sent', 'accepted', 'declined', name='version_sharing_request_status', create_type=False
)


def upgrade():
    version_sharing_request_status.create(op.get_bind())

    op.create_table(
        'version_sharing_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_code', sa.VARCHAR(length=32), nullable=False),
        sa.Column('initiator_username', sa.VARCHAR(length=256), nullable=False),
        sa.Column('receiver_username', sa.VARCHAR(length=256), nullable=True),
        sa.Column('status', version_sharing_request_status, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['version.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_version_sharing_requests_created_at'), 'version_sharing_requests', ['created_at'], unique=False
    )
    op.create_index(
        op.f('ix_version_sharing_requests_project_code'), 'version_sharing_requests', ['project_code'], unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_version_sharing_requests_project_code'), table_name='version_sharing_requests')
    op.drop_index(op.f('ix_version_sharing_requests_created_at'), table_name='version_sharing_requests')
    op.drop_table('version_sharing_requests')

    version_sharing_request_status.drop(op.get_bind())
