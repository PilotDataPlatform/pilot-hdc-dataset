# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest
from starlette.requests import Request

from dataset.services.metadata import MetadataService


@pytest.fixture
def metadata_service() -> MetadataService:
    request = Request(scope={'type': 'http', 'headers': [(b'authorization', b'Bearer eyJhbGc')]})
    return MetadataService(request)
