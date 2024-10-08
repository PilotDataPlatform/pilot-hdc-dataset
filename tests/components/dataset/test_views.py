# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import random
from datetime import datetime
from datetime import timedelta
from itertools import islice
from uuid import UUID

import pytest

from dataset.components import ModelList
from dataset.components.dataset.parameters import DatasetSortByFields
from dataset.components.sorting import SortingOrder


class TestDatasetViews:
    async def test_get_dataset_that_doesnt_exist_returns_not_found(self, client):
        response = await client.get('/v1/datasets/any')

        assert response.status_code == 404

        received_dataset = response.json()

        assert received_dataset == {'error': {'code': 'dataset.not_found', 'details': 'Dataset is not found'}}

    async def test_get_dataset_returns_dataset_by_id(self, client, dataset_factory):
        created_dataset = await dataset_factory.create()
        response = await client.get(f'/v1/datasets/{created_dataset.id}')

        assert response.status_code == 200

        received_dataset = response.json()

        assert received_dataset['id'] == str(created_dataset.id)

    async def test_get_dataset_returns_dataset_by_code(self, client, dataset_factory):
        created_dataset = await dataset_factory.create()
        response = await client.get(f'/v1/datasets/{created_dataset.code}')

        assert response.status_code == 200

        received_dataset = response.json()

        assert received_dataset['id'] == str(created_dataset.id)
        assert received_dataset['code'] == str(created_dataset.code)

    async def test_list_datasets_returns_list_of_existing_datasets(self, client, jq, dataset_factory):
        created_dataset = await dataset_factory.create()

        response = await client.get('/v1/datasets/')

        assert response.status_code == 200

        body = jq(response)
        received_dataset_id = body('.result[].id').first()
        received_total = body('.total').first()

        assert received_dataset_id == str(created_dataset.id)
        assert received_total == 1

    @pytest.mark.parametrize('sort_by', DatasetSortByFields.values())
    @pytest.mark.parametrize('sort_order', SortingOrder.values())
    async def test_list_datasets_returns_results_sorted_by_field_with_proper_order(
        self, sort_by, sort_order, client, jq, dataset_factory
    ):
        created_datasets = await dataset_factory.bulk_create(3)
        field_values = created_datasets.get_field_values(sort_by)
        if sort_by == 'created_at':
            field_values = [key.strftime('%Y-%m-%dT%H:%M:%S') for key in field_values]
        expected_values = sorted(field_values, reverse=sort_order == SortingOrder.DESC)

        response = await client.get('/v1/datasets/', query_string={'sort_by': sort_by, 'sort_order': sort_order})

        body = jq(response)
        received_values = body(f'.result[].{sort_by}').all()
        received_total = body('.total').first()

        assert received_values == expected_values
        assert received_total == 3

    @pytest.mark.parametrize('parameter', ['creator', 'code'])
    async def test_list_datasets_returns_dataset_filtered_by_parameter_full_match(
        self, parameter, client, jq, dataset_factory
    ):
        created_datasets = await dataset_factory.bulk_create(3)
        dataset = created_datasets.pop()

        response = await client.get('/v1/datasets/', query_string={parameter: getattr(dataset, parameter)})
        body = jq(response)
        received_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert received_ids == [str(dataset.id)]
        assert received_total == 1

    async def test_list_datasets_returns_datasets_filtered_by_created_at_start_and_created_at_end_parameters(
        self, client, jq, faker, dataset_factory
    ):
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)

        [await dataset_factory.create(created_at=faker.date_between_dates(two_weeks_ago, week_ago)) for _ in range(2)]
        dataset = await dataset_factory.create(created_at=faker.date_time_between_dates(week_ago, today))

        params = {
            'created_at_start': int(datetime.timestamp(week_ago)),
            'created_at_end': int(datetime.timestamp(today)),
        }
        response = await client.get('/v1/datasets/', query_string=params)

        body = jq(response)
        received_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert received_ids == [str(dataset.id)]
        assert received_total == 1

    async def test_list_datasets_returns_dataset_filtered_by_ids(self, client, jq, dataset_factory):
        created_datasets = await dataset_factory.bulk_create(5)
        ids = [str(dataset.id) for dataset in created_datasets][:-2]
        response = await client.get('/v1/datasets/', query_string={'ids': ','.join(ids)})
        body = jq(response)
        received_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert received_ids == ids
        assert received_total == 3

    async def test_list_datasets_returns_dataset_filtered_by_project_id(self, client, jq, faker, dataset_factory):
        project_id = faker.uuid4()
        await dataset_factory.create_with_project(project_id=project_id)
        await dataset_factory.create_with_project(project_id=project_id)
        dataset_without_project = await dataset_factory.create()

        response = await client.get('/v1/datasets/', query_string={'project_id': str(project_id)})
        body = jq(response)
        received_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert dataset_without_project.id not in received_ids
        assert received_total == 2

    @pytest.mark.parametrize('parameter', ['ids', 'project_id_any'])
    async def test_list_datasets_returns_422_status_code_when_ids_in_parameters_are_not_uuid(
        self, parameter, client, dataset_factory
    ):
        values = ['aaa', 'bbb']
        response = await client.get('/v1/datasets/', query_string={parameter: ','.join(values)})

        assert response.status_code == 422
        assert response.json() == {
            'error': [{'detail': 'badly formed hexadecimal UUID string', 'source': [parameter], 'title': 'value_error'}]
        }

    async def test_list_datasets_returns_datasets_with_code_specified_in_code_any_parameter(
        self, client, jq, dataset_factory
    ):
        created_datasets = await dataset_factory.bulk_create(3)
        mapping = created_datasets.map_by_field('code')

        dataset_codes = [str(i) for i in islice(mapping.keys(), 2)]
        response = await client.get('/v1/datasets/', query_string={'code_any': ','.join(dataset_codes)})

        body = jq(response)
        received_codes = body('.result[].code').all()
        received_total = body('.total').first()

        assert set(received_codes) == set(dataset_codes)
        assert received_total == 2

    async def test_list_datasets_returns_datasets_with_code_specified_in_code_any_parameter_even_if_only_one_matches(
        self, client, jq, faker, dataset_factory
    ):
        created_datasets = await dataset_factory.bulk_create(2)
        dataset = created_datasets.pop()

        dataset_codes = [faker.pystr(), faker.pystr(), dataset.code]
        response = await client.get('/v1/datasets/', query_string={'code_any': ','.join(dataset_codes)})

        body = jq(response)
        received_codes = body('.result[].code').all()
        received_total = body('.total').first()

        assert received_codes == [dataset.code]
        assert received_total == 1

    async def test_list_datasets_returns_datasets_filtered_by_project_id_any_parameter(
        self, client, jq, dataset_factory
    ):
        created_datasets = ModelList([await dataset_factory.create_with_project() for _ in range(3)])
        mapping = created_datasets.map_by_field('project_id', key_type=str)

        project_ids = random.sample(mapping.keys(), 2)
        response = await client.get('/v1/datasets/', query_string={'project_id_any': ','.join(project_ids)})

        body = jq(response)
        received_project_ids = body('.result[].project_id').all()
        received_total = body('.total').first()

        assert set(received_project_ids) == set(project_ids)
        assert received_total == 2

    async def test_list_datasets_returns_datasets_filtered_by_project_id_any_parameter_even_if_only_one_matches(
        self, client, jq, faker, dataset_factory
    ):
        created_datasets = ModelList([await dataset_factory.create_with_project() for _ in range(2)])
        dataset = created_datasets.pop()

        project_ids = [faker.uuid4(), faker.uuid4(), str(dataset.project_id)]
        response = await client.get('/v1/datasets/', query_string={'project_id_any': ','.join(project_ids)})

        body = jq(response)
        received_project_ids = body('.result[].project_id').all()
        received_total = body('.total').first()

        assert received_project_ids == [str(dataset.project_id)]
        assert received_total == 1

    async def test_list_datasets_returns_dataset_filtered_by_or_creator_parameter(self, client, jq, dataset_factory):
        created_datasets = await dataset_factory.bulk_create(2)
        dataset = created_datasets.pop()

        params = {'or_creator': dataset.creator}
        response = await client.get('/v1/datasets/', query_string=params)

        body = jq(response)
        received_ids = body('.result[].id').all()
        received_total = body('.total').first()

        assert received_ids == [str(dataset.id)]
        assert received_total == 1

    async def test_list_datasets_returns_datasets_filtered_by_creator_and_or_creator_parameters_at_once(
        self, client, jq, dataset_factory
    ):
        created_datasets = await dataset_factory.bulk_create(3)
        dataset_1, dataset_2, _ = created_datasets

        params = {'creator': dataset_1.creator, 'or_creator': dataset_2.creator}
        response = await client.get('/v1/datasets/', query_string=params)

        body = jq(response)
        received_ids = body('.result[].id').all(to=set, each_to=UUID)
        received_total = body('.total').first()

        assert received_ids == {dataset_1.id, dataset_2.id}
        assert received_total == 2

    async def test_list_datasets_returns_datasets_filtered_by_several_parameters_and_or_creator_parameter_at_once(
        self, client, jq, faker, dataset_factory
    ):
        creator_1 = faker.unique.user_name()
        creator_2 = faker.unique.user_name()
        creator_1_dataset, *_ = [await dataset_factory.create_with_project(creator=creator_1) for _ in range(2)]
        creator_2_datasets = await dataset_factory.bulk_create(2, creator=creator_2)
        creator_2_datasets_ids = creator_2_datasets.get_field_values('id')

        params = {'project_id': creator_1_dataset.project_id, 'creator': creator_1, 'or_creator': creator_2}
        response = await client.get('/v1/datasets/', query_string=params)

        body = jq(response)
        received_ids = body('.result[].id').all(to=set, each_to=UUID)
        received_total = body('.total').first()

        assert received_ids == {creator_1_dataset.id, *creator_2_datasets_ids}
        assert received_total == 3
