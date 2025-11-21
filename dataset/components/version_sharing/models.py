# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from uuid import uuid4

from sqlalchemy import VARCHAR
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dataset.components.models import DBModel
from dataset.components.types import StrEnum


class VersionSharingRequestStatus(StrEnum):
    SENT = 'sent'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class VersionSharingRequest(DBModel):
    """Version Sharing Request model."""

    __tablename__ = 'version_sharing_requests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey('version.id', ondelete='CASCADE'), nullable=False)
    project_code = Column(VARCHAR(length=32), index=True, nullable=False)
    initiator_username = Column(VARCHAR(length=256), nullable=False)
    receiver_username = Column(VARCHAR(length=256), nullable=True)
    status = Column(
        ENUM(
            VersionSharingRequestStatus,
            name='version_sharing_request_status',
            values_callable=lambda enum: enum.values(),
        ),
        default=VersionSharingRequestStatus.SENT,
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), index=True, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    version = relationship('Version', back_populates='sharing_requests')

    @property
    def dataset_id(self) -> UUID:
        return self.version.dataset_id

    @property
    def dataset_code(self) -> str:
        return self.version.dataset_code

    @property
    def source_project_id(self) -> UUID:
        return self.version.dataset.project_id

    @property
    def version_number(self) -> str:
        return self.version.version

    def get_username_for_activity_log(self) -> str:
        if self.status is VersionSharingRequestStatus.SENT:
            return self.initiator_username

        return self.receiver_username

    def get_changes_for_activity_log(self) -> list[dict[str, Any]]:
        return [
            {
                'sharing_request_id': str(self.id),
                'project_code': self.project_code,
                'status': self.status.value,
            }
        ]
