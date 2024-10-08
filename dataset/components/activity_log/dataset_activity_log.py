# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.services.activity_log import ActivityLogService


class BaseDatasetActivityLog(ActivityLogService):

    topic = 'dataset.activity'
    avro_schema_path = 'dataset/components/activity_log/dataset.activity.avsc'
