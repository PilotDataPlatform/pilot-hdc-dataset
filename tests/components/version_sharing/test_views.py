# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random

import pytest

from dataset.components.sorting import SortingOrder
from dataset.components.version_sharing.models import VersionSharingRequestStatus
from dataset.components.version_sharing.parameters import VersionSharingRequestSortByFields


class TestVersionSharingRequestViews:

    @pytest.mark.parametrize(
        'items_number,page,page_size,expected_count',
        [
            (4, 0, 3, 3),
            (4, 1, 3, 1),
            (2, 0, 3, 2),
            (2, 1, 1, 1),
            (2, 2, 1, 0),
        ],
    )
    async def test_list_version_sharing_requests_returns_properly_paginated_response(
        self,
        items_number,
        page,
        page_size,
        expected_count,
        client,
        jq,
        version_factory,
        version_sharing_request_factory,
    ):
        version = await version_factory.create_with_dataset()
        await version_sharing_request_factory.bulk_create(items_number, version_id=version.id)

        response = await client.get('/v1/version-sharing-requests/', params={'page': page, 'page_size': page_size})

        assert response.status_code == 200

        body = jq(response)
        received_version_sharing_request_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert len(received_version_sharing_request_ids) == expected_count
        assert received_total == items_number

    @pytest.mark.parametrize('sort_by', VersionSharingRequestSortByFields.values())
    @pytest.mark.parametrize('sort_order', SortingOrder.values())
    async def test_list_version_sharing_requests_returns_results_sorted_by_field_with_proper_order(
        self, sort_by, sort_order, client, jq, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        created_version_sharing_requests = await version_sharing_request_factory.bulk_create(3, version_id=version.id)
        field_values = created_version_sharing_requests.get_field_values(sort_by)
        if sort_by == 'created_at':
            field_values = [key.strftime('%Y-%m-%dT%H:%M:%S') for key in field_values]
        expected_values = sorted(field_values, reverse=sort_order == SortingOrder.DESC)

        response = await client.get(
            '/v1/version-sharing-requests/', params={'sort_by': sort_by, 'sort_order': sort_order}
        )

        assert response.status_code == 200

        body = jq(response)
        received_values = body(f'.result[].{sort_by}').all()
        received_total = body('.total').first()

        assert received_values == expected_values
        assert received_total == 3

    @pytest.mark.parametrize('parameter', ['project_code'])
    async def test_list_version_sharing_requests_returns_results_filtered_by_parameter_full_text_match(
        self, parameter, client, jq, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        created_version_sharing_requests = await version_sharing_request_factory.bulk_create(3, version_id=version.id)
        version_sharing_request = random.choice(created_version_sharing_requests)

        response = await client.get(
            '/v1/version-sharing-requests/', params={parameter: getattr(version_sharing_request, parameter)}
        )

        assert response.status_code == 200

        body = jq(response)
        received_ids = body('.result[].id').all()

        assert received_ids == [str(version_sharing_request.id)]

    async def test_get_version_sharing_request_by_id_returns_version_sharing_request_object(
        self, client, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        created_version_sharing_request = await version_sharing_request_factory.create(version_id=version.id)

        response = await client.get(f'/v1/version-sharing-requests/{created_version_sharing_request.id}')

        assert response.status_code == 200

        received_version_sharing_request = response.json()

        assert received_version_sharing_request['id'] == str(created_version_sharing_request.id)

    async def test_create_version_sharing_request_creates_new_version_sharing_request_object_with_sent_status(
        self, client, jq, version_factory, version_sharing_request_factory, version_sharing_request_crud
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = version_sharing_request_factory.generate(version_id=version.id)

        payload = version_sharing_request.to_payload()
        response = await client.post('/v1/version-sharing-requests/', json=payload)

        assert response.status_code == 200

        body = jq(response)
        received_version_sharing_request_id = body('.id').first()
        created_version_sharing_request = await version_sharing_request_crud.retrieve_by_id(
            received_version_sharing_request_id
        )

        assert created_version_sharing_request.project_code == version_sharing_request.project_code
        assert created_version_sharing_request.status == VersionSharingRequestStatus.SENT

    async def test_create_version_sharing_request_returns_unprocessable_entity_response_when_status_is_not_sent(
        self, client, jq, version_factory, version_sharing_request_factory, version_sharing_request_crud
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = version_sharing_request_factory.generate(
            version_id=version.id, status=VersionSharingRequestStatus.ACCEPTED
        )

        payload = version_sharing_request.to_payload()
        response = await client.post('/v1/version-sharing-requests/', json=payload)

        assert response.status_code == 422

        body = jq(response)

        assert body('.detail[].ctx').first() == {'given': 'accepted', 'permitted': ['sent']}

    async def test_update_version_sharing_request_updates_version_sharing_request_status_and_receiver_username(
        self, client, jq, fake, version_factory, version_sharing_request_factory, version_sharing_request_crud
    ):
        version = await version_factory.create_with_dataset()
        created_version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.SENT
        )
        receiver_username = fake.user_name()

        payload = {'status': VersionSharingRequestStatus.ACCEPTED, 'receiver_username': receiver_username}
        response = await client.patch(
            f'/v1/version-sharing-requests/{created_version_sharing_request.id}', json=payload
        )

        assert response.status_code == 200

        body = jq(response)
        received_version_sharing_request_id = body('.id').first()
        received_version_sharing_request = await version_sharing_request_crud.retrieve_by_id(
            received_version_sharing_request_id
        )

        assert received_version_sharing_request.status == VersionSharingRequestStatus.ACCEPTED
        assert received_version_sharing_request.receiver_username == receiver_username

    async def test_start_version_sharing_request_calls_queue_service(
        self, client, jq, fake, httpx_mock, authorization_header, version_factory, version_sharing_request_factory
    ):
        version = await version_factory.create_with_dataset()
        created_version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.ACCEPTED
        )
        httpx_mock.add_response(method='POST', url='http://queue_service/v1/send_message', status_code=200, json={})

        payload = {'job_id': fake.uuid4(), 'session_id': fake.uuid4()}
        response = await client.post(
            f'/v1/version-sharing-requests/{created_version_sharing_request.id}/start',
            json=payload,
            headers=authorization_header,
        )

        assert response.status_code == 204
