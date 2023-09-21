# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

import pytest

from dataset.config import get_settings
from dataset.dependencies import get_s3_client


@pytest.mark.parametrize(
    'file_name,file_body',
    [
        ('test_folder.csv', 'a,b,c1,2,3'),
        ('test_folder.json', '{"test": "test1"}'),
        ('test_folder.csv2', 'a|b|c1|2|3'),
        ('test_folder.tsv', 'a,b,c1,2,3'),
    ],
)
async def test_preview_should_respect_file_type(
    minio_container, client, httpx_mock, file_name, file_body, authorization_header
):
    bucket_name = str(uuid4())
    s3_client = await get_s3_client()
    await s3_client.create_bucket(bucket_name)
    await s3_client.boto_client.upload_object(bucket_name, file_name, file_body)

    file_geid = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-164.8138467'
    httpx_mock.add_response(
        method='GET',
        url='http://metadata_service/v1/item/6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-164.8138467/',
        json={
            'result': {
                'id': file_geid,
                'storage': {'location_uri': f'minio://http://10.3.7.220/{bucket_name}/{file_name}'},
                'name': file_name,
                'size': 1,
            }
        },
    )
    res = await client.get(f'/v1/{file_geid}/preview', headers=authorization_header)
    assert res.status_code == 200
    response_content = res.json()['result']['content'].replace('\n', '').replace('\r', '')
    assert response_content == file_body


async def test_preview_should_return_404_when_file_not_found(client, httpx_mock, authorization_header):

    httpx_mock.add_response(
        method='GET',
        url='http://metadata_service/v1/item/any/',
        json={'result': {}},
    )
    res = await client.get('/v1/any/preview', headers=authorization_header)
    assert res.status_code == 404
    assert res.json() == {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}


@pytest.fixture
async def long_file(minio_container):
    bucket_name = 'bucket'
    file_name = 'file.tx'
    file_body = ''
    for i in range(int(500000 / 4)):
        file_body += f'\n{i}, {i+1}, {i+2}, {i+3}, {i+4}, {i+5}'
    s3_client = await get_s3_client()
    await s3_client.create_bucket(bucket_name)
    await s3_client.boto_client.upload_object(bucket_name, file_name, file_body)
    return bucket_name, file_name, file_body


async def test_preview_should_concatenate_true_when_file_size_bigger_than_conf(
    long_file, client, httpx_mock, authorization_header
):
    settings = get_settings()

    bucket_name, file_name, file_body = long_file
    file_id = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-164.8138467'

    httpx_mock.add_response(
        method='GET',
        url=f'http://metadata_service/v1/item/{file_id}/',
        json={
            'result': {
                'id': file_id,
                'storage': {'location_uri': f'minio://http://10.3.7.220/{bucket_name}/{file_name}'},
                'name': file_name,
                'size': settings.MAX_PREVIEW_SIZE + 1,
            }
        },
    )
    res = await client.get(f'/v1/{file_id}/preview', headers=authorization_header)
    assert res.status_code == 200
    assert res.json()['result']['is_concatenated']
    assert res.json()['result']['content'] != file_body


@pytest.mark.parametrize(
    'file_name,file_body',
    [
        ('test_folder.csv', 'a,b,c1,2,3'),
        ('test_folder.json', '{"test": "test1"}'),
        ('test_folder.tsv', 'a,b,c1,2,3'),
    ],
)
async def test_preview_stream_should_return_stream_and_200(
    client, httpx_mock, minio_container, file_name, file_body, authorization_header
):
    bucket_name = str(uuid4())
    s3_client = await get_s3_client()
    await s3_client.create_bucket(bucket_name)
    await s3_client.boto_client.upload_object(bucket_name, file_name, file_body)

    file_geid = '6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-164.8138467'
    httpx_mock.add_response(
        method='GET',
        url='http://metadata_service/v1/item/6c99e8bb-ecff-44c8-8fdc-a3d0ed7ac067-164.8138467/',
        json={
            'result': {
                'id': file_geid,
                'storage': {'location_uri': f'minio://http://10.3.7.220/{bucket_name}/{file_name}'},
                'name': file_name,
                'size': 1,
            }
        },
    )
    res = await client.get(f'/v1/{file_geid}/preview/stream', headers=authorization_header)
    assert res.text == file_body
    assert res.status_code == 200


async def test_preview_stream_should_return_404_when_file_not_found(client, httpx_mock, authorization_header):

    httpx_mock.add_response(
        method='GET',
        url='http://metadata_service/v1/item/any/',
        json={'result': {}},
    )
    res = await client.get('/v1/any/preview/stream', headers=authorization_header)
    assert res.status_code == 404
    assert res.json() == {'error': {'code': 'global.not_found', 'details': 'Requested resource is not found'}}
