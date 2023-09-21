# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import os
from typing import Any

import boto3
import pytest
from botocore.client import ClientError
from docker.errors import DockerException
from testcontainers.core.container import DockerContainer

from dataset.config import get_settings

MINIO_DOCKER_IMAGE = 'minio/minio:RELEASE.2022-05-03T20-36-08Z'
settings = get_settings()


class MinioContainer(DockerContainer):
    """Minio docker container for testing."""

    def __init__(self, image: str) -> None:
        super().__init__(image)

        self.env = {
            'MINIO_ROOT_USER': settings.S3_ACCESS_KEY,
            'MINIO_ROOT_PASSWORD': settings.S3_SECRET_KEY,
        }
        self.ports = {'9000/tcp': 9100, '9101/tcp': 9101}
        volume_suffix = os.urandom(5).hex()
        self.volumes = {f'test-data-{volume_suffix}-{i}': {'bind': f'/data{i}'} for i in range(1, 5)}
        self._command = 'minio server /data{1...4} --console-address ":9101"'

    def stop(self, **kwargs: Any) -> None:
        super().stop(**kwargs)
        for volume_name in self.volumes.keys():
            try:
                self._docker.client.volumes.get(volume_name).remove()
            except DockerException:
                pass


class S3TestClient:
    """Simple boto3 S3 client to test buckets and files."""

    def __init__(self) -> None:
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )

    def check_if_bucket_exists(self, bucket: str) -> bool:
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False

    def check_if_file_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False


@pytest.fixture
def s3_test_client() -> S3TestClient:
    yield S3TestClient()


@pytest.fixture(scope='session')
def minio_container() -> MinioContainer:
    with MinioContainer(MINIO_DOCKER_IMAGE) as container:
        yield container
