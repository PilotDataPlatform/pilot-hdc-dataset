# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
import os
import shutil
import time
from datetime import datetime

from aioredis import StrictRedis
from sqlalchemy.future import select
from starlette.concurrency import run_in_threadpool

from dataset.components.exceptions import AlreadyExists
from dataset.components.file.locks import LockingManager
from dataset.components.folder.crud import FolderCRUD
from dataset.components.object_storage.s3 import S3Client
from dataset.components.schema.models import SchemaDataset
from dataset.components.version.activity_log import VersionActivityLog
from dataset.components.version.crud import VersionCRUD
from dataset.components.version.schemas import VersionCreateSchema
from dataset.components.version.schemas import VersionSchema
from dataset.config import get_settings
from dataset.logger import logger
from dataset.services.metadata import MetadataService

settings = get_settings()


class VersionPublisher(object):
    """Class that runs in background, creating the zip in minio and a new version in the database."""

    TMP_BASE = '/tmp/'

    def __init__(
        self,
        redis_client: StrictRedis,
        version_crud: VersionCRUD,
        locking_manager: LockingManager,
        folder_crud: FolderCRUD,
        metadata_service: MetadataService,
        s3_client: S3Client,
        activity_log: VersionActivityLog,
    ):
        self.dataset_files = []
        self.s3_client = s3_client
        self.version_crud = version_crud
        self.locking_manager = locking_manager
        self.folder_crud = folder_crud
        self.metadata_service = metadata_service
        self.redis_client = redis_client
        self.activity_log = activity_log
        self.job_key = None
        self.zip_path = None
        self.tmp_folder = self.TMP_BASE + str(time.time())

    async def create_job(self, job_key: str) -> None:
        """Ensure only one version is created by dataset at time."""
        job = await self.redis_client.get(job_key)
        if job:
            dict_job = json.loads(job)
            if dict_job['status'] == 'inprogress':
                raise AlreadyExists()
        self.job_key = job_key

    async def _update_status(self, status, error_msg=''):
        """Updates job status in redis."""
        redis_status = json.dumps(
            {
                'status': status,
                'error_msg': error_msg,
            }
        )
        await self.redis_client.set(self.job_key, redis_status, ex=1 * 60 * 60)

    def _parse_minio_location(self, location):
        """Extract bucket and object key from minio path."""

        minio_path = location.split('//')[-1]
        _, bucket, obj_path = tuple(minio_path.split('/', 2))
        return {'bucket': bucket, 'path': obj_path}

    async def _add_schemas(self, dataset_id: str):
        """Saves schema json files to folder that will zipped."""
        db_session = self.version_crud.session
        if not os.path.isdir(self.tmp_folder):
            os.makedirs(self.tmp_folder + '/data')

        query = select(SchemaDataset).where(SchemaDataset.dataset_id == dataset_id, SchemaDataset.is_draft.is_(False))
        query_default = query.where(SchemaDataset.standard == 'default')
        query_open_minds = query.where(SchemaDataset.standard == 'open_minds')

        schemas_default = (await db_session.execute(query_default)).scalars().all()
        schemas_open_minds = (await db_session.execute(query_open_minds)).scalars().all()

        for schema in schemas_default:
            with open(self.tmp_folder + '/default_' + schema.name, 'w') as w:
                w.write(json.dumps(schema.content, indent=4, ensure_ascii=False))

        for schema in schemas_open_minds:
            with open(self.tmp_folder + '/openMINDS_' + schema.name, 'w') as w:
                w.write(json.dumps(schema.content, indent=4, ensure_ascii=False))

    async def publish(self, dataset_code: str, dataset_id: str, version_data: VersionCreateSchema):
        """Background job that creates the zip all files and create the dataset version."""
        await self._update_status('inprogress')
        self.zip_path = f'{self.TMP_BASE}{dataset_code}_{str(datetime.now())}'
        try:
            # lock file here
            level1_nodes = await self.folder_crud.get_children(dataset_code, None)
            locked_node, err = await self.locking_manager.recursive_lock_publish(level1_nodes)
            if err:
                logger.error('Error occured while calling recursive_lock_publish.')
                raise err
            self.dataset_files = await self.metadata_service.get_files(dataset_code)
            await self._download_dataset_files()
            await self._add_schemas(str(dataset_id))
            await run_in_threadpool(self._zip_files)
            minio_location = await self._upload_version(dataset_code)
            version_schema = VersionSchema(
                notes=version_data.notes,
                created_by=version_data.operator,
                version=version_data.version,
                dataset_code=dataset_code,
                dataset_id=dataset_id,
                location=minio_location,
            )
            dataset_version = await self.version_crud.create(version_schema)

            logger.info(f'Successfully published {dataset_id} version {version_data.version}')
            await self.activity_log.send_publish_version_succeed(dataset_version)
            await self._update_status('success')
        except Exception as e:
            error_msg = f'Error publishing {dataset_id}: {str(e)}'
            logger.exception(error_msg)
            await self._update_status('failed', error_msg=error_msg)
        finally:
            # unlock the nodes if we got blocked
            for resource_key, operation in locked_node:
                await self.locking_manager.unlock_resource(resource_key, operation)
        return

    async def _download_dataset_files(self):
        """Download files from minio."""
        file_paths = []
        for file in self.dataset_files:
            location_data = self._parse_minio_location(file['storage']['location_uri'])
            await self.s3_client.download_file(
                location_data['bucket'], location_data['path'], self.tmp_folder + '/' + location_data['path']
            )
            file_paths.append(self.tmp_folder + '/' + location_data['path'])
        return file_paths

    def _zip_files(self):
        """Create zip file."""
        shutil.make_archive(self.zip_path, 'zip', self.tmp_folder)
        return self.zip_path

    async def _upload_version(self, dataset_code: str):
        """Upload version zip to minio."""
        bucket = dataset_code
        file_path = 'versions/' + self.zip_path.split('/')[-1] + '.zip'
        with open(f'{self.zip_path}.zip', mode='rb') as file:
            await self.s3_client.upload_file(bucket, file_path, file)

        minio_http = ('https://' if settings.S3_INTERNAL_HTTPS else 'http://') + settings.S3_INTERNAL
        minio_location = f'minio://{minio_http}/{bucket}/{file_path}'
        return minio_location
