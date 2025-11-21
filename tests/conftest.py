# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from starlette.config import environ

environ['QUEUE_SERVICE'] = 'http://QUEUE_SERVICE'
environ['DATA_OPS_UTIL'] = 'http://DATA_OPS_UTIL'
environ['METADATA_SERVICE'] = 'http://METADATA_SERVICE'
environ['PROJECT_SERVICE'] = 'http://PROJECT_SERVICE'
environ['ROOT_PATH'] = './tests/'
environ['S3_INTERNAL'] = 'MINIO_ENDPOINT'

pytest_plugins = [
    'tests.fixtures.services.base',
    'tests.fixtures.services.metadata',
    'tests.fixtures.db',
    'tests.fixtures.fake',
    'tests.fixtures.kafka',
    'tests.fixtures.redis',
    'tests.fixtures.policy',
    'tests.fixtures.app',
    'tests.fixtures.s3',
    'tests.fixtures.jq',
    'tests.fixtures.components.dataset',
    'tests.fixtures.components.schema_template',
    'tests.fixtures.components.schema',
    'tests.fixtures.components.version',
    'tests.fixtures.components.bids_result',
    'tests.fixtures.components.version_sharing',
]
