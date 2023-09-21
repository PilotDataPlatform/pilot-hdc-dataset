# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import copy

import pytest
from fastapi import HTTPException

from dataset.components.exceptions import NotFound
from dataset.components.file.schemas import ItemStatusSchema


@pytest.fixture
def item():
    return {
        'id': 'fd571f18-a62a-44b1-927c-91ad662260ac',
        'parent': '84634d30-66aa-4c8b-84f4-ebe3016f59a7',
        'parent_path': 'admin',
        'restore_path': None,
        'status': ItemStatusSchema.ACTIVE.name,
        'type': 'file',
        'name': 'file1.txt',
        'owner': 'admin',
        'container_code': 'indoctestproject',
        'container_type': 'project',
        'zone': 1,
    }


class TestMetadataService:
    async def test_return_item_by_dataset_code(self, httpx_mock, metadata_service, item):
        dataset_code = 'testdataset'
        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/'
                f'?recursive=true&zone=1&container_code={dataset_code}&container_type=dataset&page_size=100&page=0'
            ),
            json={'page': 0, 'num_of_pages': 1, 'result': [item]},
        )
        response = await metadata_service.get_objects(dataset_code)
        assert response[0] == item

    async def test_return_item_by_id(self, httpx_mock, metadata_service, item):
        item_id = item['id']
        httpx_mock.add_response(
            method='GET',
            url=(f'http://metadata_service/v1/item/{item_id}/'),
            json={'result': [item]},
        )
        response = await metadata_service.get_by_id(item_id)
        assert response[0] == item

    async def test_raise_not_found_exception_for_nonexistent_item(self, httpx_mock, metadata_service):
        item_id = 'invalid'
        httpx_mock.add_response(
            method='GET',
            url=f'http://metadata_service/v1/item/{item_id}/',
            json={},
            status_code=404,
        )
        with pytest.raises(NotFound):
            await metadata_service.get_by_id(item_id)

    async def test_return_created_item(self, httpx_mock, metadata_service, item):
        httpx_mock.add_response(
            method='POST',
            url='http://metadata_service/v1/item/',
            json={'result': [item]},
        )
        response = await metadata_service.create_object(item)
        assert response[0] == item

    async def test_raise_exception_for_created_item(self, httpx_mock, metadata_service, item):
        httpx_mock.add_response(method='POST', url='http://metadata_service/v1/item/', json={}, status_code=500)

        with pytest.raises(HTTPException):
            await metadata_service.create_object(item)

    async def test_return_none_update_item(self, httpx_mock, metadata_service, item):
        item_id = item['id']
        httpx_mock.add_response(
            method='PUT',
            url=f'http://metadata_service/v1/item/?id={item_id}',
            json={},
        )
        response = await metadata_service.update_object(item)
        assert not response

    async def test_raise_exception_for_update_item(self, httpx_mock, metadata_service, item):
        item_id = item['id']
        httpx_mock.add_response(
            method='PUT', url=f'http://metadata_service/v1/item/?id={item_id}', json={}, status_code=500
        )
        with pytest.raises(HTTPException):
            await metadata_service.update_object(item)

    async def test_return_none_delete_item_by_id(self, httpx_mock, metadata_service, item):
        item_id = item['id']
        httpx_mock.add_response(
            method='DELETE',
            url=f'http://metadata_service/v1/item/?id={item_id}',
            json={},
        )
        response = await metadata_service.delete_object(item_id)
        assert not response

    async def test_return_files(self, httpx_mock, metadata_service, item):
        dataset_code = 'testdataset'
        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/'
                f'?recursive=true&zone=1&container_code={dataset_code}&'
                f'container_type=dataset&page_size=100&page=0&type=file'
            ),
            json={'page': 0, 'num_of_pages': 1, 'result': [item]},
        )
        response = await metadata_service.get_files(dataset_code)
        assert response == [item]

    async def test_return_files_should_return_files_from_all_pages(self, httpx_mock, metadata_service, item):
        dataset_code = 'testdataset'
        item2 = copy.deepcopy(item)
        item2['name'] = 'file2.txt'
        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/'
                f'?recursive=true&zone=1&container_code={dataset_code}&container_type=dataset&page_size=100&page=0'
            ),
            json={'page': 0, 'num_of_pages': 2, 'result': [item]},
        )
        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/'
                f'?recursive=true&zone=1&container_code={dataset_code}&container_type=dataset&page_size=100&page=1'
            ),
            json={'page': 1, 'num_of_pages': 2, 'result': [item2]},
        )
        response = await metadata_service.get_objects(dataset_code)
        assert response == [item, item2]

    async def test_return_True_for_duplicated_item(self, httpx_mock, metadata_service, item):
        dataset_code = 'testdataset'
        folder_name = item['name']

        httpx_mock.add_response(
            method='GET',
            url=(
                'http://metadata_service/v1/items/search/'
                f'?recursive=true&zone=1&container_code={dataset_code}'
                f'&container_type=dataset&page_size=100&page=0&name={folder_name}'
            ),
            json={'page': 0, 'num_of_pages': 1, 'result': [item]},
        )
        response = await metadata_service.is_duplicated_name_item(dataset_code, folder_name, item['parent'])
        assert response
