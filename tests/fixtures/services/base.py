# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any

import jwt
import pytest


@pytest.fixture
def authorization_header(fake) -> dict[str, Any]:
    token = jwt.encode({'preferred_username': fake.user_name()}, key='')
    return {'Authorization': f'Bearer {token}'}
