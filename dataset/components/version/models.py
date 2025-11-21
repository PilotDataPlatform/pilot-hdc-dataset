# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dataset.components.models import DBModel


class Version(DBModel):
    """Version database model."""

    __tablename__ = 'version'
    __table_args__ = (UniqueConstraint('dataset_id', 'version', name='dataset_id_version_unique'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dataset_code = Column(String())
    dataset_id = Column(UUID(as_uuid=True), ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False)
    version = Column(String())
    created_by = Column(String())
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    location = Column(String())
    notes = Column(String())

    dataset = relationship('Dataset', back_populates='versions')
    sharing_requests = relationship('VersionSharingRequest', back_populates='version', cascade='all,delete-orphan')

    @property
    def filename(self) -> str:
        """Return the filename of the version zip file."""

        return Path(self.location).name
