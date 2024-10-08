# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dataset.components.models import DBModel


class SchemaDataset(DBModel):
    """Schema database model."""

    __tablename__ = 'schema'
    __table_args__ = (
        UniqueConstraint(
            'name',
            'dataset_id',
            name='name_dataset_id_unique',
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String())
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id'))
    schema_template_id = Column(UUID(as_uuid=True), ForeignKey('schema_template.id'))
    standard = Column(String())
    system_defined = Column(Boolean())
    is_draft = Column(Boolean())
    content = Column(JSONB())
    create_timestamp = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    update_timestamp = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    creator = Column(String())

    schema_template = relationship('SchemaTemplate', back_populates='schemas')
    dataset = relationship('Dataset', back_populates='schemas')
