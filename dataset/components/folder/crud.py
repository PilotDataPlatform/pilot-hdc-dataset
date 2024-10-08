# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from dataset.components.exceptions import AlreadyExists
from dataset.components.folder.schemas import FolderCreateSchema
from dataset.components.folder.schemas import FolderMetadataCreateSchema
from dataset.components.folder.schemas import FolderResponseSchema
from dataset.components.object_storage.s3 import S3Client
from dataset.services.metadata import MetadataService


class FolderCRUD:
    """Class for managing folders."""

    def __init__(self, s3_client: S3Client, metadata_service: MetadataService):
        self.s3_client = s3_client
        self.metadata_service = metadata_service

    async def _create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send folder data to Metadata Service."""
        return await self.metadata_service.create_object(data)

    async def get_new_parent_metadata(self, parent_id: str) -> Tuple[str, str]:
        """Get new parent_path and parent_id."""

        new_parent_path = None
        new_parent_id = None

        if parent_id:
            folder_node = await self.metadata_service.get_by_id(parent_id)

            new_parent_path = folder_node['name']
            if folder_node['parent_path']:
                new_parent_path = folder_node['parent_path'] + '/' + folder_node['name']
            new_parent_id = folder_node['id']
        return new_parent_path, new_parent_id

    async def create_folder(self, data: FolderCreateSchema, dataset_code: str) -> FolderResponseSchema:
        """Create node in metadata."""

        parent_path, parent_id = await self.get_new_parent_metadata(data.parent_folder_geid)
        does_name_exist = await self.metadata_service.is_duplicated_name_item(dataset_code, data.folder_name, parent_id)
        if does_name_exist:
            raise AlreadyExists()

        payload = FolderMetadataCreateSchema(
            parent=parent_id,
            parent_path=parent_path,
            name=data.folder_name,
            owner=data.username,
            container_code=dataset_code,
        ).dict()
        folder = await self._create(payload)
        return FolderResponseSchema(**folder)

    async def import_folder(
        self,
        parent_id: Dict[str, Any],
        parent_path: str,
        owner: str,
        name: str,
        dataset_code: str,
    ) -> Dict[str, Any]:
        """Add a folder to dataset from import task."""

        folder_data = FolderMetadataCreateSchema(
            parent=parent_id,
            parent_path=parent_path,
            name=name,
            owner=owner,
            container_code=dataset_code,
        )
        return await self._create(folder_data.dict())

    async def get_children(self, code: str, father_id: str, items_type: str = 'dataset') -> List[Dict[str, Any]]:
        """Returns all files/folders that have father_id as parent."""

        items = await self.metadata_service.get_objects(code, items_type=items_type)
        children_items = []

        for item in items:
            if item['parent'] == father_id:
                children_items.append(item)

        return children_items
