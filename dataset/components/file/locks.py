# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from typing import Optional

import httpx
from fastapi import HTTPException

from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.file.schemas import ResourceLockingSchema
from dataset.components.folder.crud import FolderCRUD
from dataset.config import get_settings
from dataset.logger import logger

settings = get_settings()


class LockingManager:
    """Manages resource locking."""

    DATAOPS_LOCK_URL = f'{settings.DATA_UTILITY_SERVICE_v2}/resource/lock/'

    def __init__(self, folder_crud: FolderCRUD):
        self.folder_crud = folder_crud

    async def lock_resource(self, resource_key: str, operation: str) -> None:
        """Lock specified resource for reading or writing."""
        logger.info('Lock resource:', extra={'resource_key': resource_key})
        resource_lock = ResourceLockingSchema(resource_key=resource_key, operation=operation)
        async with httpx.AsyncClient() as client:
            response = await client.post(self.DATAOPS_LOCK_URL, json=dict(resource_lock))
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response:
                logger.exception(f'resource {resource_key} already in use')
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json()) from exc
            raise exc

    async def unlock_resource(self, resource_key: str, operation: str) -> None:
        """Unlock specified resource for reading or writing."""
        logger.info('Unlock resource:', extra={'resource_key': resource_key})
        resource_unlock = ResourceLockingSchema(resource_key=resource_key, operation=operation)
        async with httpx.AsyncClient() as client:
            response = await client.request(url=self.DATAOPS_LOCK_URL, json=dict(resource_unlock), method='DELETE')
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response:
                logger.exception(f'Error when unlock resource {resource_key}')
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json()) from exc
            raise exc

    async def recursive_lock_import(  # noqa: C901
        self, dataset_code, nodes, root_path
    ) -> tuple[list[Any], Optional[Exception]]:
        """the function will recursively lock the node tree OR unlock the tree base on the parameter.

        - if lock = true then perform the lock
        - if lock = false then perform the unlock
        """
        # this is for crash recovery, if something trigger the exception
        # we will unlock the locked node only. NOT the whole tree. The example
        # case will be copy the same node, if we unlock the whole tree in exception
        # then it will affect the processing one.
        locked_node, err = [], None

        async def recur_walker(current_nodes, current_root_path, new_name=None) -> None:
            """recursively trace down the node tree and run the lock function."""
            for ff_object in current_nodes:
                # update here if the folder/file is archieved then skip
                if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                    continue

                # conner case here, we DONT lock the name folder
                # for the copy we will lock the both source as read operation,
                # and the target will be write operation
                if ff_object.get('parent_path') != ff_object.get('owner'):
                    bucket, minio_obj_path = None, None
                    if ff_object.get('type').lower() == 'file':
                        minio_path = ff_object.get('storage').get('location_uri').split('//')[-1]
                        _, bucket, minio_obj_path = tuple(minio_path.split('/', 2))
                    else:
                        bucket = 'core-' + ff_object.get('container_code')
                        parent_path = ff_object.get('parent_path')
                        if parent_path:
                            try:
                                parent_path = parent_path.split('/', 1)[1]
                            except IndexError:
                                pass
                            minio_obj_path = '%s/%s' % (parent_path, ff_object.get('name'))
                        else:
                            minio_obj_path = '%s' % ff_object.get('name')
                    # source is from project
                    source_key = '{}/{}'.format(bucket, minio_obj_path)
                    await self.lock_resource(source_key, 'read')
                    locked_node.append((source_key, 'read'))

                # open the next recursive loop if it is folder
                if ff_object.get('type').lower() == 'folder':
                    if new_name:
                        filename = new_name
                    else:
                        filename = ff_object.get('name')

                    if current_root_path == settings.DATASET_FILE_FOLDER:
                        next_root_path = filename
                    else:
                        next_root_path = current_root_path + '/' + filename
                    children_nodes = await self.folder_crud.get_children(
                        ff_object['container_code'], ff_object.get('id', None), ff_object['container_type']
                    )
                    await recur_walker(children_nodes, next_root_path)

            return

        # start here
        try:
            await recur_walker(nodes, root_path)
        except Exception as e:
            err = e

        return locked_node, err

    async def recursive_lock_delete(self, nodes) -> tuple[list[Any], Optional[Exception]]:  # noqa: C901
        """Recursively lock resources to be deleted."""
        # this is for crash recovery, if something trigger the exception
        # we will unlock the locked node only. NOT the whole tree. The example
        # case will be copy the same node, if we unlock the whole tree in exception
        # then it will affect the processing one.
        locked_node, err = [], None

        async def recur_walker(current_nodes) -> None:
            """recursively trace down the node tree and run the lock function."""
            for ff_object in current_nodes:
                # update here if the folder/file is archieved then skip
                if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                    continue

                # conner case here, we DONT lock the name folder
                # for the copy we will lock the both source as read operation,
                # and the target will be write operation
                if ff_object.get('parent_path') != ff_object.get('owner'):
                    bucket, minio_obj_path = None, None
                    if ff_object.get('type').lower() == 'file':
                        minio_path = ff_object.get('storage').get('location_uri').split('//')[-1]
                        _, bucket, minio_obj_path = tuple(minio_path.split('/', 2))
                    else:
                        bucket = ff_object.get('container_code')
                        parent_path = ff_object.get('parent_path')
                        minio_obj_path = '%s/' % settings.DATASET_FILE_FOLDER
                        if parent_path:
                            try:
                                parent_path = parent_path.split('/', 1)[1]
                            except IndexError:
                                pass
                            minio_obj_path += '%s/%s' % (parent_path, ff_object.get('name'))
                        else:
                            minio_obj_path += '%s' % ff_object.get('name')

                    source_key = '{}/{}'.format(bucket, minio_obj_path)
                    await self.lock_resource(source_key, 'write')
                    locked_node.append((source_key, 'write'))

                # open the next recursive loop if it is folder
                if ff_object.get('type').lower() == 'folder':
                    children_nodes = await self.folder_crud.get_children(
                        ff_object['container_code'], ff_object.get('id', None)
                    )
                    await recur_walker(children_nodes)

            return

        # start here
        try:
            await recur_walker(nodes)
        except Exception as e:
            err = e

        return locked_node, err

    async def recursive_lock_move_rename(  # noqa: C901
        self, nodes, root_path, new_name=None
    ) -> tuple[list[Any], Optional[Exception]]:
        """Recursively lock resource to be renamed."""
        # this is for crash recovery, if something trigger the exception
        # we will unlock the locked node only. NOT the whole tree. The example
        # case will be copy the same node, if we unlock the whole tree in exception
        # then it will affect the processing one.
        locked_node, err = [], None

        # TODO lock
        async def recur_walker(current_nodes, current_root_path, new_name=None) -> None:
            """recursively trace down the node tree and run the lock function."""
            for ff_object in current_nodes:
                # update here if the folder/file is archieved then skip
                if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                    continue

                # conner case here, we DONT lock the name folder
                # for the copy we will lock the both source as read operation,
                # and the target will be write operation
                if ff_object.get('parent_path') != ff_object.get('owner'):
                    bucket, minio_obj_path = None, None
                    if ff_object.get('type').lower() == 'file':
                        minio_path = ff_object.get('storage').get('location_uri').split('//')[-1]
                        _, bucket, minio_obj_path = tuple(minio_path.split('/', 2))
                    else:
                        bucket = ff_object.get('container_code')
                        if ff_object['parent_path']:
                            parent_path = ff_object['parent_path']
                            minio_obj_path = '%s/%s/%s' % (
                                settings.DATASET_FILE_FOLDER,
                                parent_path,
                                ff_object.get('name'),
                            )
                        else:
                            minio_obj_path = '%s/%s' % (settings.DATASET_FILE_FOLDER, ff_object.get('name'))
                    source_key = '{}/{}'.format(bucket, minio_obj_path)
                    await self.lock_resource(source_key, 'write')
                    locked_node.append((source_key, 'write'))

                    if current_root_path == settings.DATASET_FILE_FOLDER:
                        target_key = '{}/{}/{}'.format(
                            bucket, current_root_path, new_name if new_name else ff_object.get('name')
                        )
                    else:
                        target_key = '{}/{}/{}/{}'.format(
                            bucket,
                            settings.DATASET_FILE_FOLDER,
                            current_root_path,
                            new_name if new_name else ff_object.get('name'),
                        )
                    await self.lock_resource(target_key, 'write')
                    locked_node.append((target_key, 'write'))

                # open the next recursive loop if it is folder
                if ff_object.get('type').lower() == 'folder':
                    if new_name:
                        filename = new_name
                    else:
                        filename = ff_object.get('name')

                    if current_root_path == settings.DATASET_FILE_FOLDER:
                        next_root_path = filename
                    else:
                        next_root_path = current_root_path + '/' + filename
                    children_nodes = await self.folder_crud.get_children(
                        ff_object['container_code'], ff_object.get('id', None), ff_object['container_type']
                    )
                    await recur_walker(children_nodes, next_root_path)

            return

        # start here
        try:
            await recur_walker(nodes, root_path, new_name)
        except Exception as e:
            err = e

        return locked_node, err

    async def recursive_lock_publish(self, nodes) -> tuple[list[Any], Optional[Exception]]:
        """Recursively lock resource to be published."""

        # this is for crash recovery, if something trigger the exception
        # we will unlock the locked node only. NOT the whole tree. The example
        # case will be copy the same node, if we unlock the whole tree in exception
        # then it will affect the processing one.
        locked_node, err = [], None

        async def recur_walker(current_nodes) -> None:
            """recursively trace down the node tree and run the lock function."""
            for ff_object in current_nodes:
                # update here if the folder/file is archieved then skip
                if ff_object['status'] == ItemStatusSchema.ARCHIVED.name:
                    continue

                # conner case here, we DONT lock the name folder
                # for the copy we will lock the both source as read operation,
                # and the target will be write operation
                if ff_object.get('parent_path') != ff_object.get('owner'):
                    bucket, minio_obj_path = None, None
                    if ff_object.get('type').lower() == 'file':
                        minio_path = ff_object.get('storage').get('location_uri').split('//')[-1]
                        _, bucket, minio_obj_path = tuple(minio_path.split('/', 2))
                    else:
                        bucket = ff_object.get('container_code')
                        minio_obj_path = '%s/%s' % (settings.DATASET_FILE_FOLDER, ff_object.get('name'))

                    source_key = '{}/{}'.format(bucket, minio_obj_path)
                    await self.lock_resource(source_key, 'read')
                    locked_node.append((source_key, 'read'))

                # open the next recursive loop if it is folder
                if ff_object.get('type').lower() == 'folder':
                    # next_root = current_root_path+"/"+(new_name if new_name else ff_object.get("name"))
                    children_nodes = await self.folder_crud.get_children(
                        ff_object['container_code'], ff_object.get('id', None)
                    )
                    await recur_walker(children_nodes)

            return

        # start here
        try:
            await recur_walker(nodes)
        except Exception as e:
            err = e

        return locked_node, err
