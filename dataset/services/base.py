# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict

import httpx
from fastapi import Request

from dataset.components.exceptions import Unauthorized


class BaseService:
    """Base class for managing service calls."""

    def __init__(self, request: Request):
        self.headers = request.headers

    def _get_authorization_token(self) -> str:
        """Retrieve token from authorization header."""
        token = self.headers.get('Authorization')
        if not token:
            raise Unauthorized()
        return token

    async def get(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Retrieve request for service."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers={'Authorization': self._get_authorization_token()})
        response.raise_for_status()

        return response.json()

    async def create(self, url: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create request for service."""
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers={'Authorization': self._get_authorization_token()})
        response.raise_for_status()

        return response.json()

    async def update(self, url: str, payload: Dict[str, Any] = None, params: Dict[str, Any] = None) -> None:
        """Update request for service."""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url, json=payload, params=params, headers={'Authorization': self._get_authorization_token()}
            )
        response.raise_for_status()

    async def delete(self, url: str, params: Dict[str, Any] = None) -> None:
        """Delete request for service."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url, params=params, headers={'Authorization': self._get_authorization_token()}
            )
        response.raise_for_status()
