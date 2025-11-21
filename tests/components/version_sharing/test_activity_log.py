# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import io

from fastavro import schema as avro_schema
from fastavro import schemaless_reader

from dataset.components.activity_log.schemas import DatasetActivityLogSchema
from dataset.components.version_sharing.activity_log import VersionSharingActivityLog
from dataset.components.version_sharing.models import VersionSharingRequestStatus


class TestVersionSharingActivityLog:

    async def test_send_publish_version_succeed_should_send_correct_msg(
        self,
        version_factory,
        version_sharing_request_factory,
        kafka_producer_client,
        kafka_dataset_consumer,
    ):
        version = await version_factory.create_with_dataset()
        version_sharing_request = await version_sharing_request_factory.create(
            version_id=version.id, status=VersionSharingRequestStatus.ACCEPTED
        )

        version_activity_log = VersionSharingActivityLog(kafka_producer_client=kafka_producer_client)
        await version_activity_log.send_sharing_request_update(version_sharing_request)

        msg = await kafka_dataset_consumer.getone()

        schema_loaded = avro_schema.load_schema('dataset/components/activity_log/dataset.activity.avsc')
        activity_log = schemaless_reader(io.BytesIO(msg.value), schema_loaded)

        activity_log_schema = DatasetActivityLogSchema.parse_obj(activity_log)

        assert activity_log_schema.version == version.version
        assert activity_log_schema.container_code == version.dataset.code
        assert activity_log_schema.user == version_sharing_request.receiver_username
        assert not activity_log_schema.target_name
        assert activity_log_schema.activity_type == 'sharing_request_update'
        assert activity_log_schema.activity_time == activity_log['activity_time']
        assert activity_log_schema.changes == activity_log['changes']
