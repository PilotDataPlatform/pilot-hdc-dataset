# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from sqlalchemy import VARCHAR
from sqlalchemy import Column
from sqlalchemy import Index
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import INTEGER
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dataset.components.models import DBModel


class Dataset(DBModel):
    """Dataset database model."""

    __tablename__ = 'datasets'
    __table_args__ = (
        UniqueConstraint('code'),
        Index('ix_datasets_dataset_created_at_creator', 'created_at', 'creator'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source = Column(VARCHAR(length=256), nullable=False)
    authors = Column(ARRAY(VARCHAR(256)), default=[], nullable=False)
    code = Column(VARCHAR(length=32), unique=True, index=True, nullable=False)
    type = Column(VARCHAR(length=256), nullable=False)
    modality = Column(ARRAY(VARCHAR(256)), default=[])
    collection_method = Column(ARRAY(VARCHAR(256)), default=[])
    license = Column(VARCHAR(length=256))
    tags = Column(ARRAY(VARCHAR(256)), default=[])
    description = Column(VARCHAR(length=5000), nullable=False)
    size = Column(INTEGER())
    total_files = Column(INTEGER())
    title = Column(VARCHAR(length=256), nullable=False)
    creator = Column(VARCHAR(length=256), index=True, nullable=False)
    project_id = Column(UUID(as_uuid=True))
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), index=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    schema_templates = relationship('SchemaTemplate', back_populates='dataset', cascade='all,delete-orphan')
    versions = relationship('Version', back_populates='dataset', cascade='all,delete-orphan', passive_deletes=True)
    schemas = relationship('SchemaDataset', back_populates='dataset', cascade='all,delete-orphan')
