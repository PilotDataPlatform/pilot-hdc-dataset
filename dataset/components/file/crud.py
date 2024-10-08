# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import csv
import json
from io import StringIO
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from starlette.concurrency import run_in_threadpool

from dataset.components.dataset.models import Dataset
from dataset.components.exceptions import NotFound
from dataset.components.file.schemas import FileSchema
from dataset.components.file.schemas import FileStreamSchema
from dataset.components.file.schemas import ItemStatusSchema
from dataset.components.folder.exceptions import FolderNotFound
from dataset.components.object_storage.s3 import S3Client
from dataset.config import get_settings
from dataset.logger import logger
from dataset.services.metadata import MetadataService

settings = get_settings()


class FileCRUD:
    """Class for managing files."""

    def __init__(self, s3_client: S3Client, metadata_service: MetadataService):
        self.s3_client = s3_client
        self.metadata_service = metadata_service

    def _parse_csv_response(self, csvdata: str) -> str:
        """Return content from csv file."""

        csv.field_size_limit(settings.MAX_PREVIEW_SIZE)
        csvfile = StringIO(csvdata)
        csv_out = StringIO()
        # detect csv format
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), [',', '|', ';', '\t'])
        except csv.Error:
            dialect = csv.excel
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        writer = csv.writer(csv_out, delimiter=',')
        writer.writerows(reader)
        content = csv_out.getvalue()
        if len(content) >= settings.MAX_PREVIEW_SIZE:
            # Remove last line as it will be incomplete
            content = content[: content[:-1].rfind('\n')]
        return content

    def _parse_location(self, path: str) -> Dict[str, str]:
        """Return bucket and object key content from csv file."""

        minio_path = path.split('//')[-1]
        _, bucket, obj_path = tuple(minio_path.split('/', 2))
        return {'bucket': bucket, 'path': obj_path}

    async def _format_file_body(self, file_type: str, body: str) -> str:
        """Return decoded content by file type."""

        if file_type in ['csv', 'tsv']:
            return await run_in_threadpool(self._parse_csv_response, body)
        if file_type == 'json':
            try:
                return json.dumps(json.loads(body))
            except ValueError:
                logger.error('fail to parse the json')
        return body

    async def _get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Return file metadata: bucket, path, path and size."""

        file_metadata = await self.metadata_service.get_by_id(file_id)
        if not file_metadata:
            raise NotFound()
        file_data = self._parse_location(file_metadata['storage']['location_uri'])
        file_type = file_metadata['name'].split('.')[1]
        return {
            'bucket': file_data['bucket'],
            'path': file_data['path'],
            'type': file_type,
            'size': file_metadata['size'],
        }

    async def download_file(self, file_id: str) -> FileSchema:
        """Return file metadata."""

        file_metadata = await self._get_file_metadata(file_id)
        file_body = await self.s3_client.get_file_body(file_metadata['bucket'], file_metadata['path'])
        content = await self._format_file_body(file_metadata['type'], file_body)
        return FileSchema(content=content, type=file_metadata['type'], size=file_metadata['size'])

    async def stream_file(self, file_id: str) -> FileStreamSchema:
        """Return file metadata for stream."""

        file_metadata = await self._get_file_metadata(file_id)
        file = await self.s3_client.boto_client.stat_object(file_metadata['bucket'], file_metadata['path'])
        return FileStreamSchema(content=file['Body'], type=file_metadata['type'], size=file_metadata['size'])

    async def create(
        self,
        dataset: Dataset,
        file: Dict[str, Any],
        owner: str,
        parent: Dict[str, Any],
        new_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add file to dataset."""

        # generate minio object path
        file_name = new_name if new_name else file.get('name')

        parent_path = parent.get('parent_path')
        if parent and dataset.id != parent['id']:
            if parent_path:
                parent_path = parent_path + '/' + parent['name']
            else:
                parent_path = parent['name']

        if parent_path:
            fuf_path = parent_path + '/' + file_name
        else:
            fuf_path = file_name
        minio_http = ('https://' if settings.S3_INTERNAL_HTTPS else 'http://') + settings.S3_INTERNAL
        location = f'minio://{minio_http}/{dataset.code}/{settings.DATASET_FILE_FOLDER}/{fuf_path}'

        payload = {
            'parent': parent.get('id'),
            'parent_path': parent_path,
            'type': 'file',
            'name': file_name,
            'owner': owner,
            'container_code': dataset.code,
            'container_type': 'dataset',
            'location_uri': location,
            'size': file.get('size', 0),
        }
        folder_node = await self.metadata_service.create_object(payload)

        # make minio copy
        try:
            # minio location is minio://http://<end_point>/bucket/user/object_path
            minio_path = file.get('storage').get('location_uri').split('//')[-1]
            _, bucket, obj_path = tuple(minio_path.split('/', 2))

            await self.s3_client.copy_object(
                bucket, obj_path, dataset.code, settings.DATASET_FILE_FOLDER + '/' + fuf_path
            )
            logger.info(f'Minio Copy {dataset.code}/{fuf_path} Success')

            payload = {'id': folder_node.get('id'), 'status': ItemStatusSchema.ACTIVE}
            await self.metadata_service.update_object(payload)

        except Exception as e:
            logger.exception(f'error when uploading: {str(e)}')
            raise e

        return folder_node

    async def delete(self, file: Dict[str, Any]) -> None:
        """Delete file from dataset."""
        await self.metadata_service.delete_object(file.get('id'))
        try:
            # minio location is minio://http://<end_point>/bucket/user/object_path
            minio_path = file['storage'].get('location_uri').split('//')[-1]
            _, bucket, obj_path = tuple(minio_path.split('/', 2))
            logger.info('call minio delete', extra={'bucket': bucket, 'obj_path': 'obj_path'})
            await self.s3_client.delete_object(bucket, obj_path)
            logger.info(f'Minio {bucket}/{obj_path} Delete Success')
        except Exception as e:
            logger.exception(f'error when deleting: {str(e)}')
            raise e

    async def validate_files_folders(
        self, file_id_list: List[Dict[str, Any]], code: str, items_type: str = 'dataset'
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """walk thought the list and validate if the file is from correct root."""

        passed_file = []
        not_passed_file = []
        duplicate_in_batch_dict = {}

        obj_list = await self.metadata_service.get_objects(code, items_type=items_type)
        # creates dict where key is obj.id and value is root_objects index
        object_ids = {obj['id']: index for index, obj in enumerate(obj_list)}

        # this is to keep track the object in passed_file array
        # and in the duplicate_in_batch_dict it will be {"geid": array_index}
        # and this can help to trace back when duplicate occur
        array_index = 0

        for file_id in file_id_list:
            # get index from dict in root_objects
            root_object_index = object_ids.get(file_id, None)

            # if there is no connect then the node is not correct
            # else it is correct
            if root_object_index is None:
                not_passed_file.append({'id': file_id, 'feedback': 'unauthorized'})

            else:
                current_node = obj_list[root_object_index]
                exist_index = duplicate_in_batch_dict.get(current_node.get('name'), None)
                # if we have process the file with same name in the same BATCH
                # we will try to update name for ALL duplicate file into display_path
                if exist_index is not None:
                    if current_node['parent_path']:
                        name = current_node.get('parent_path').replace('/', '_') + current_node.get('name')
                    else:
                        name = current_node.get('name')
                    current_node.update(
                        {
                            'feedback': 'duplicate in same batch, update the name',
                            'name': name,
                        }
                    )
                    # if the first node is not updated then use the index to trace back
                    if exist_index != -1:
                        file = passed_file[exist_index]
                        if file['parent_path']:
                            name = file.get('parent_path').replace('/', '_') + current_node.get('name')
                        else:
                            name = current_node.get('name')
                        passed_file[exist_index].update(
                            {
                                'name': name,
                                'feedback': 'duplicate in same batch, update the name',
                            }
                        )
                        # and mark the first one
                        first_geid = passed_file[exist_index].get('id')
                        duplicate_in_batch_dict.update({first_geid: -1})

                # else we just record the file for next checking
                else:
                    current_node.update({'feedback': 'exist'})
                    duplicate_in_batch_dict.update({current_node.get('name'): array_index})

                passed_file.append(current_node)
                array_index += 1
        return passed_file, not_passed_file

    async def remove_duplicate_file(
        self, files_list: List[Dict[str, Any]], dataset_code: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """mark duplicated files in dataset."""

        dataset_objects = await self.metadata_service.get_objects(dataset_code)
        duplic_file = []
        not_duplic_file = []
        name_parent_dict = {obj['name']: obj['parent_path'] for obj in dataset_objects}
        type_dict = {obj['name']: obj['type'] for obj in dataset_objects}
        for file in files_list:
            same_name = name_parent_dict.get(file.get('name'), 'not_found')
            obj_type = type_dict.get(file.get('name'), 'not_found')
            if same_name == 'not_found':
                not_duplic_file.append(file)
            elif same_name == file.get('parent_path') and obj_type == file.get('type'):
                file.update({'feedback': 'duplicate or unauthorized'})
                duplic_file.append(file)
            else:
                not_duplic_file.append(file)

        return duplic_file, not_duplic_file

    async def validate_files_target_folder(self, target_id: str, dataset_code: str) -> Dict[str, Any]:
        """Validate existence of a file(s) target folder."""
        target_folder = await self.metadata_service.get_by_id(target_id)
        if not target_folder:
            raise FolderNotFound()

        if target_folder.get('container_code') != dataset_code:
            raise FolderNotFound()
        return target_folder
