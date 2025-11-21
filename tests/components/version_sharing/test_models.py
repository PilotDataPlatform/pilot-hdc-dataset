# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.version_sharing.models import VersionSharingRequestStatus


class TestVersionSharingRequest:
    async def test_dataset_id_returns_related_dataset_id(self, version_factory, version_sharing_request_factory):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(version_id=version.id)

        assert version_sharing_request.dataset_id == version.dataset.id

    async def test_dataset_code_returns_related_dataset_code(self, version_factory, version_sharing_request_factory):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(version_id=version.id)

        assert version_sharing_request.dataset_code == version.dataset.code

    async def test_source_project_id_returns_related_project_id(self, version_factory, version_sharing_request_factory):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(version_id=version.id)

        assert version_sharing_request.source_project_id == version.dataset.project_id

    async def test_version_number_returns_related_version(self, version_factory, version_sharing_request_factory):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(version_id=version.id)

        assert version_sharing_request.version_number == version.version

    async def test_get_username_for_activity_log_returns_initiator_username_when_status_is_sent(
        self, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.SENT
        )

        assert version_sharing_request.get_username_for_activity_log() == version_sharing_request.initiator_username

    async def test_get_username_for_activity_log_returns_receiver_username_when_status_is_not_sent(
        self, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.ACCEPTED
        )

        assert version_sharing_request.get_username_for_activity_log() == version_sharing_request.receiver_username

    async def test_get_changes_for_activity_log_returns_dictionary_with_expected_changes(
        self, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.ACCEPTED
        )
        expected_changes = [
            {
                'sharing_request_id': str(version_sharing_request.id),
                'project_code': version_sharing_request.project_code,
                'status': version_sharing_request.status.value,
            }
        ]

        assert version_sharing_request.get_changes_for_activity_log() == expected_changes
