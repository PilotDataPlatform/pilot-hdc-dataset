# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
"""Change project_id to not nullable.

Revision ID: 0013
Revises: 0012
Create Date: 2024-12-19 18:29:07.893365
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from alembic.operations.schemaobj import SchemaObjects
from alembic.runtime.migration import MigrationContext
from sqlalchemy import func
from sqlalchemy import update
from sqlalchemy.dialects import postgresql
from sqlalchemy.future import select

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = '0012'


def load_datasets_table(context: MigrationContext) -> sa.Table:
    schema = SchemaObjects(context)
    return schema.table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
    )


def is_dataset_without_project_id_exist(context: MigrationContext, datasets: sa.Table) -> bool:
    count = context.connection.execute(select(func.count()).where(datasets.c.project_id.is_not(None))).scalar_one()

    return bool(count)


def is_project_id_exist(context: MigrationContext, datasets: sa.Table, project_id: UUID) -> bool:
    result = context.connection.execute(select(datasets.c.id).where(datasets.c.project_id == project_id)).fetchone()
    return result is not None


def get_project_id(context: MigrationContext, datasets: sa.Table) -> UUID:
    """Get project id from the hardcoded list or use the most used."""

    project_ids = [
        UUID('63aac575-14eb-4448-b784-22253e23608b'),  # DEV indoctestproject
        UUID('c50dc274-edc2-43c6-9a2a-1b7263c8a8ab'),  # PROD hdctestproject
    ]

    for project_id in project_ids:
        if is_project_id_exist(context, datasets, project_id):
            return project_id

    top_used_projects = context.connection.execute(
        select(func.count(), datasets.c.project_id)
        .where(datasets.c.project_id.is_not(None))
        .group_by(datasets.c.project_id)
        .order_by(func.count().desc())
    ).fetchone()

    if top_used_projects is not None:
        return top_used_projects[1]

    raise Exception('Project id is not found')


def upgrade():
    context = op.get_context()
    datasets = load_datasets_table(context)

    if is_dataset_without_project_id_exist(context, datasets):
        project_id = get_project_id(context, datasets)

        context.connection.execute(
            update(datasets).where(datasets.c.project_id.is_(None)).values({datasets.c.project_id: project_id})
        )

    op.alter_column('datasets', 'project_id', nullable=False)


def downgrade():
    op.alter_column('datasets', 'project_id', nullable=True)
