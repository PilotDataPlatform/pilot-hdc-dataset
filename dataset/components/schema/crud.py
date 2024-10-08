# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import List

from sqlalchemy import select
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import Select

from dataset.components.crud import CRUD
from dataset.components.dataset.models import Dataset
from dataset.components.exceptions import AlreadyExists
from dataset.components.exceptions import ServiceException
from dataset.components.schema.exceptions import SchemaNotFound
from dataset.components.schema.models import SchemaDataset
from dataset.components.schema.schemas import POSTSchema
from dataset.components.schema.schemas import POSTSchemaList
from dataset.components.schema.schemas import SchemaResponse
from dataset.components.schema_template.crud import SchemaTemplateCRUD
from dataset.config import get_settings

settings = get_settings()


class SchemaCRUD(CRUD):
    """CRUD for managing schema template database models."""

    model = SchemaDataset
    db_error_codes: dict[str, ServiceException] = {
        '23503': SchemaNotFound(),  # missing foreign key
        '23505': AlreadyExists(),  # duplicated entry
    }

    @property
    def select_query(self) -> Select:
        """Return base select including join with Dataset model."""

        return select(self.model).outerjoin(Dataset).options(contains_eager(self.model.dataset))

    async def get_schema_list(self, request_payload: POSTSchemaList) -> List[SchemaResponse]:
        """Get List of Schemas with the essential schema on top."""
        filter_allowed = [
            'name',
            'dataset_id',
            'schema_template_id',
            'standard',
            'system_defined',
            'is_draft',
            'create_timestamp',
            'update_timestamp',
            'creator',
        ]
        query = select(self.model)
        for key in filter_allowed:
            filter_val = getattr(request_payload, key)
            if filter_val is not None:
                query = query.where(getattr(self.model, key) == filter_val)
        schemas_fetched = await self._retrieve_many(query)

        result = [SchemaResponse.from_orm(record) for record in schemas_fetched]
        # essentials rank top
        essentials = [record for record in result if record.name == settings.ESSENTIALS_NAME]
        not_essentials = [record for record in result if record.name != settings.ESSENTIALS_NAME]
        if len(essentials) > 0:
            essentials_schema = essentials[0]
            not_essentials.insert(0, essentials_schema)
        return not_essentials

    async def create_essentials(self, dataset: Dataset) -> SchemaDataset:
        """Create dataset essentials schema."""

        schema_template_crud = SchemaTemplateCRUD(self.session)
        schema_template = await schema_template_crud.get_template_by_name(settings.ESSENTIALS_TEMPLATE_NAME)

        schema_data = POSTSchema(
            **{
                'name': settings.ESSENTIALS_NAME,
                'dataset_geid': str(dataset.id),
                'tpl_geid': str(schema_template.id),
                'standard': schema_template.standard,
                'system_defined': schema_template.system_defined,
                'is_draft': False,
                'content': {
                    'dataset_title': dataset.title,
                    'dataset_authors': dataset.authors,
                    'dataset_type': dataset.type,
                    'dataset_modality': dataset.modality,
                    'dataset_collection_method': dataset.collection_method,
                    'dataset_license': dataset.license,
                    'dataset_description': dataset.description,
                    'dataset_tags': dataset.tags,
                    'dataset_code': dataset.code,
                },
                'creator': dataset.creator,
            }
        )
        return await self.create(schema_data)
