# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from dataset.components.bids_result.schemas import BIDSResultResponseSchema

pytestmark = pytest.mark.asyncio


async def test_dataset_verify_pre_should_return_200_and_response_from_queue_service(
    client, httpx_mock, dataset_factory, authorization_header
):
    dataset = await dataset_factory.create()
    dataset_code = dataset.code
    httpx_mock.add_response(method='POST', url='http://queue_service/v1/send_message', json={'any': 'any'})

    payload = {'dataset_code': dataset_code, 'type': 'any'}
    res = await client.post('/v1/dataset/verify/pre', json=payload, headers=authorization_header)
    assert res.status_code == 200
    assert res.json() == {'result': {'any': 'any'}}


async def test_get_bids_msg_should_not_found_should_return_404(client):
    dataset_code = 'utdataset'
    res = await client.get(f'/v1/dataset/bids-msg/{dataset_code}')
    assert res.status_code == 404
    assert res.json() == {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}


async def test_get_bids_msg_should_return_200(client, bids_result_factory):
    bids_results = await bids_result_factory.create(dataset_code='any')
    res = await client.get(f'/v1/dataset/bids-msg/{bids_results.dataset_code}')
    expected_bids_result = BIDSResultResponseSchema.from_orm(bids_results).to_payload()

    assert res.status_code == 200
    assert res.json()['result'] == expected_bids_result


async def test_create_a_new_bids_result_should_return_200(client):
    dataset_code = 'utbidsdataset'
    payload = {'validate_output': {'result': 'any'}}
    res = await client.put(
        f'/v1/dataset/bids-result/{dataset_code}',
        headers={'Authorization': 'Barear token', 'Refresh-Token': 'refresh_token'},
        json=payload,
    )

    assert res.status_code == 200
    assert res.json()['validate_output'] == {'result': 'any'}


async def test_update_a_bids_result_should_return_200(client, dataset_factory, bids_result_factory):
    bid_results = await bids_result_factory.create(dataset_code='any')
    dataset_code = bid_results.dataset_code
    dataset = await dataset_factory.create()
    dataset_code = dataset.code
    payload = {'validate_output': {'result': 'updated one'}}
    res = await client.put(
        f'/v1/dataset/bids-result/{dataset_code}',
        headers={'Authorization': 'Barear token', 'Refresh-Token': 'refresh_token'},
        json=payload,
    )

    assert res.status_code == 200
    assert res.json()['validate_output'] == {'result': 'updated one'}
