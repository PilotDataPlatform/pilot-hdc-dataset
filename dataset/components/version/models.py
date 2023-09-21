# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dataset.components.models import DBModel


class Version(DBModel):
    """Version database model."""

    __tablename__ = 'version'
    __table_args__ = (UniqueConstraint('dataset_id', 'version', name='dataset_id_version_unique'),)

    id = Column(Integer, primary_key=True)
    dataset_code = Column(String())
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False)
    version = Column(String())
    created_by = Column(String())
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    location = Column(String())
    notes = Column(String())

    dataset = relationship('Dataset', back_populates='versions')
