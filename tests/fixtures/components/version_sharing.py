# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.version_sharing.crud import VersionSharingRequestCRUD
from dataset.components.version_sharing.models import VersionSharingRequest
from dataset.components.version_sharing.models import VersionSharingRequestStatus
from dataset.components.version_sharing.schemas import VersionSharingRequestSchema
from tests.fixtures.components import CRUDFactory


class VersionSharingRequestFactory(CRUDFactory):
    def generate(
        self,
        *,
        version_id: UUID = ...,
        project_code: str = ...,
        initiator_username: str = ...,
        receiver_username: str = ...,
        status: VersionSharingRequestStatus = ...,
    ) -> VersionSharingRequestSchema:
        if version_id is ...:
            version_id = self.fake.uuid4(cast_to=None)

        if project_code is ...:
            project_code = self.fake.container_code()

        if initiator_username is ...:
            initiator_username = self.fake.user_name()

        if receiver_username is ...:
            receiver_username = self.fake.user_name()

        if status is ...:
            status = VersionSharingRequestStatus.SENT

        return VersionSharingRequestSchema(
            version_id=version_id,
            project_code=project_code,
            initiator_username=initiator_username,
            receiver_username=receiver_username,
            status=status,
        )

    async def create(
        self,
        *,
        version_id: UUID = ...,
        project_code: str = ...,
        initiator_username: str = ...,
        receiver_username: str = ...,
        status: VersionSharingRequestStatus = ...,
        **kwds: Any,
    ) -> VersionSharingRequest:
        entry = self.generate(
            version_id=version_id,
            project_code=project_code,
            initiator_username=initiator_username,
            receiver_username=receiver_username,
            status=status,
        )

        return await self.crud.create(entry, **kwds)

    async def bulk_create(
        self,
        number: int,
        *,
        version_id: UUID = ...,
        project_code: str = ...,
        initiator_username: str = ...,
        receiver_username: str = ...,
        status: VersionSharingRequestStatus = ...,
        **kwds: Any,
    ) -> ModelList[VersionSharingRequest]:
        return ModelList(
            [
                await self.create(
                    version_id=version_id,
                    project_code=project_code,
                    initiator_username=initiator_username,
                    receiver_username=receiver_username,
                    status=status,
                    **kwds,
                )
                for _ in range(number)
            ]
        )


@pytest.fixture
def version_sharing_request_crud(db_session) -> VersionSharingRequestCRUD:
    return VersionSharingRequestCRUD(db_session)


@pytest.fixture
async def version_sharing_request_factory(
    version_sharing_request_crud, fake
) -> AsyncGenerator[VersionSharingRequestFactory]:
    version_sharing_request_factory = VersionSharingRequestFactory(version_sharing_request_crud, fake)
    yield version_sharing_request_factory
    await version_sharing_request_factory.truncate_table()
