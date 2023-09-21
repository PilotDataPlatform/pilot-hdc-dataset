# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import asyncio
from typing import Any
from typing import Dict
from typing import List

import httpx
from fastapi import HTTPException

from dataset.components.exceptions import NotFound
from dataset.config import get_settings
from dataset.logger import logger
from dataset.services.base import BaseService

settings = get_settings()


class MetadataService(BaseService):
    """Class to access Metadata Service."""

    SERVICE_NAME = 'MetadataService'
    BASE_URL = settings.METADATA_SERVICE
    ITEM_URL = f'{BASE_URL}/v1/item/'
    SEARCH_URL = f'{BASE_URL}/v1/items/search/'

    async def get_objects(
        self, code: str, items_type: str = 'dataset', extra: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """List items by container_code."""
        page = 0
        params = {
            'recursive': True,
            'zone': 1,
            'container_type': items_type,
            'page_size': 100,
            'page': page,
            'container_code': code,
        }
        if extra:
            params.update(**extra)
        response = await self.get(self.SEARCH_URL, params)
        total_pages = response['num_of_pages']
        objects_list = response['result']
        if total_pages > 1:
            tasks = []
            for page in range(1, total_pages):
                params['page'] = page
                task = asyncio.create_task(self.get(self.SEARCH_URL, params))
                tasks.append(task)
                results = await asyncio.gather(*tasks)
                for response in results:
                    objects_list.extend(response['result'])
        return objects_list

    async def get_by_id(self, id_: str) -> Dict[str, Any]:
        """Get item by id in medatadata service."""

        url = f'{self.ITEM_URL}{id_}/'
        try:
            return (await self.get(url))['result']
        except httpx.HTTPStatusError as exc:
            if exc.response:
                if exc.response.status_code == 404:
                    raise NotFound()
            raise exc

    async def create_object(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Creates item in medatadata service."""

        payload.update({'zone': 1})
        if not payload.get('parent'):
            payload['parent_path'] = None

        try:
            logger.info(f'Metadata request: {self.ITEM_URL}', extra={'payload': payload})
            response = await self.create(self.ITEM_URL, payload)
        except httpx.HTTPStatusError as exc:
            if exc.response:
                logger.exception('error when creating item metadata', extra={'payload': payload})
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json()) from exc
            raise exc
        item = response['result']
        return item

    async def update_object(self, payload: Dict[str, Any]) -> None:
        """Updates item in metadata service."""
        try:
            logger.info(f'Metadata update request: {self.ITEM_URL}', extra={'payload': payload})
            await self.update(url=self.ITEM_URL, payload=payload, params={'id': payload['id']})
        except httpx.HTTPStatusError as exc:
            if exc.response:
                logger.exception('error when updating item metadata', extra={'payload': payload})
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json()) from exc
            raise exc

    async def delete_object(self, id_: str) -> None:
        """Deletes item in metadata service."""
        try:
            logger.info(f'Metadata delete request: {self.ITEM_URL}', extra={'id': id_})
            await self.delete(url=self.ITEM_URL, params={'id': id_})
        except httpx.HTTPStatusError as exc:
            if exc.response:
                logger.exception('error when deleting item metadata', extra={'id': id_})
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json()) from exc
            raise exc

    async def get_files(self, code: str) -> List[Dict[str, Any]]:
        """Return all files from dataset."""
        return await self.get_objects(code, extra={'type': 'file'})

    async def is_duplicated_name_item(self, code: str, name: str, parent_id: str) -> bool:
        """Returns True when there is another item with the same name under the same parent."""

        items = await self.get_objects(code, extra={'name': name})
        for item in items:
            if item['parent'] == parent_id:
                return True
