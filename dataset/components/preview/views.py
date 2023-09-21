# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import StreamingResponse

from dataset.components.file.crud import FileCRUD
from dataset.components.file.dependencies import get_file_crud
from dataset.components.preview.schemas import LegacyPreviewResultResponseSchema
from dataset.components.preview.schemas import PreviewResponseSchema
from dataset.config import get_settings
from dataset.logger import logger

settings = get_settings()
router = APIRouter(tags=['Preview'])


@router.get(
    '/{file_id}/preview',
    response_model=LegacyPreviewResultResponseSchema,
    summary='CSV/JSON/TSV File preview',
)
async def get_preview(file_id: str, file_crud: FileCRUD = Depends(get_file_crud)):
    """Get file preview."""
    logger.info(f'Get preview for: {str(file_id)}')
    file = await file_crud.download_file(file_id)
    if file.size >= settings.MAX_PREVIEW_SIZE:
        is_concatenated = True
    else:
        is_concatenated = False
    preview_schema = PreviewResponseSchema(content=file.content, type=file.type, is_concatenated=is_concatenated)

    return LegacyPreviewResultResponseSchema(result=preview_schema)


@router.get(
    '/{file_id}/preview/stream',
    summary='CSV/JSON/TSV File preview stream',
    response_class=StreamingResponse,
)
async def stream(file_id: str, file_crud: FileCRUD = Depends(get_file_crud)):
    """Get a file preview stream."""
    logger.info(f'Get preview for: {str(file_id)}')

    file_stream = await file_crud.stream_file(file_id)
    if file_stream.type in ['csv', 'tsv']:
        mimetype = 'text/csv'
    else:
        mimetype = 'application/json'

    return StreamingResponse(file_stream.content, media_type=mimetype)
