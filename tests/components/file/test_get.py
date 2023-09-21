# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from dataset.components.file.schemas import ItemStatusSchema

pytestmark = pytest.mark.asyncio


async def test_get_dataset_files_should_return_404_when_dataset_not_found(client):
    dataset_id = str(uuid4())
    res = await client.get(f'/v1/dataset/{dataset_id}/files')
    assert res.json() == {'error': {'code': 'dataset.not_found', 'details': 'Dataset is not found'}}
    assert res.status_code == 404


async def test_get_dataset_files(client, httpx_mock, dataset_factory, authorization_header):
    dataset = await dataset_factory.create()
    dataset_geid = str(dataset.id)
    file_geid = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-1648138467'
    file = {
        'type': 'file',
        'storage': {'location_uri': 'http://anything.com/bucket/obj/path'},
        'id': file_geid,
        'owner': 'me',
        'parent_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'parent': None,
        'dataset_code': dataset.code,
    }

    httpx_mock.add_response(
        method='GET',
        url=(
            'http://metadata_service/v1/items/search/'
            f'?recursive=true&zone=1&container_code={dataset.code}&container_type=dataset&page_size=100&page=0'
        ),
        json={'page': 0, 'num_of_pages': 1, 'result': [file]},
    )

    res = await client.get(f'/v1/dataset/{dataset_geid}/files', headers=authorization_header)
    assert res.status_code == 200
    assert res.json() == {
        'result': {
            'data': [file],
            'route': [],
        },
        'total': 1,
    }
