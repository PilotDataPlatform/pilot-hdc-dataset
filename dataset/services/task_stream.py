# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from time import time
from typing import Any

import httpx

from dataset.components.file.types import EActionType
from dataset.components.file.types import EFileStatus
from dataset.components.file.types import FileStatus
from dataset.config import get_settings
from dataset.logger import logger

settings = get_settings()


class TaskStreamService:

    TASK_URL = settings.DATA_UTILITY_SERVICE_V1 + '/task-stream/'

    async def _write_file_status_event(self, file_status: FileStatus) -> dict[str, Any]:
        """Send file status to DataOps to be written into Redis."""

        post_json = file_status.dict()
        async with httpx.AsyncClient() as client:
            res = await client.post(self.TASK_URL, json=post_json)
        if res.status_code != 200:
            raise Exception(f'Send file status error {res.status_code}: {res.text}')
        logger.info('Created file status', extra={'payload': post_json, 'url': self.TASK_URL})
        return res.json()

    def _extract_uuid(self, s: str) -> str:
        """Removes the action type and timestamp from a job identifier string."""

        for action_type in EActionType:
            s = s.replace(f'{action_type.name}-', '')
        s = re.sub('-\\d{10}$', '', s)
        return s

    async def _create_job_status(
        self,
        session_id: str,
        source_file: list[dict[str, Any]],
        action: EActionType,
        status: EFileStatus,
        dataset_code: str,
    ) -> str:
        """Creates and returns a job status dictionary with information about a file operation."""

        source_geid = source_file.get('id')
        return_id = action + '-' + source_geid + '-' + str(int(time()))

        job_id = self._extract_uuid(source_geid)
        target_name = source_file['name']
        if source_file['parent_path']:
            target_name = f'{source_file["parent_path"]}/{source_file["name"]}'
        file_status = FileStatus(
            session_id=session_id,
            target_names=[target_name],
            target_type=source_file.get('type'),
            container_code=dataset_code,
            container_type='dataset',
            action_type=action,
            status=status,
            job_id=job_id,
        )
        await self._write_file_status_event(file_status)
        return {source_geid: return_id}

    async def initialize_file_jobs(
        self, session_id: str, action: EActionType, batch_list: list[dict[str, Any]], dataset_code: str
    ) -> dict[str, Any]:
        """Creates and sends the initial status of a batch of files to the DataOps service to be written into Redis."""

        job_ids = {}
        session_id = 'local_test' if not session_id else session_id
        for file_object in batch_list:
            item_id = file_object['id']
            logger.info('initialize_file_jobs', extra={'file': file_object})
            tracker = await self._create_job_status(
                session_id, file_object, action, EFileStatus.WAITING.name, dataset_code
            )
            job_ids[item_id] = tracker[item_id]

        return {'session_id': session_id, 'action': action, 'job_id': job_ids}

    async def update_job_status(
        self,
        session_id: str,
        source_file: dict[str, Any],
        action: EActionType,
        status: EFileStatus,
        dataset_code,
        job_id: str,
    ) -> dict[str, Any]:
        """Updates the status of a file job and sends it to the DataOps service to be written into Redis."""

        logger.info('update_job_status', extra={'file': source_file, 'job_id': job_id, 'status': status})
        job_id = self._extract_uuid(job_id)
        target_name = source_file['name']
        if source_file['parent_path']:
            target_name = f'{source_file["parent_path"]}/{source_file["name"]}'
        file_status = FileStatus(
            session_id=session_id,
            target_names=[target_name],
            target_type=source_file.get('type'),
            container_code=dataset_code,
            container_type='dataset',
            action_type=action,
            status=status,
            job_id=job_id,
        )
        res = await self._write_file_status_event(file_status)
        return res
