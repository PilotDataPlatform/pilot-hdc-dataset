# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import Field
from pydantic import constr

from dataset.components.schemas import BaseSchema
from dataset.components.schemas import ListResponseSchema
from dataset.config import get_settings

settings = get_settings()


class Modality(str, Enum):
    ANATOMICAL_APPROACH = 'anatomical approach'
    NEUROIMAGING = 'neuroimaging'
    MICROSCOPY = 'microscopy'
    HISTOLOGICAL_APPROACH = 'histological approach'
    NEURAL_CONNECTIVITY = 'neural connectivity'
    MOLECULAR_EXPRESSION_CHARACTERIZATION = 'molecular expression characterization'
    MULTIMODAL_APPROACH = 'multimodal approach'
    ELECTROPHYSIOLOGY = 'electrophysiology'
    BEHAVIORAL_APPROACH = 'behavioral approach'
    MOLECULAR_EXPRESSION_APPROACH = 'molecular expression approach'
    CELL_POPULATION_IMAGING = 'cell population imaging'
    PHYSIOLOGICAL_APPROACH = 'physiological approach'
    MORPHOLOGICAL_APPROACH = 'morphological approach'
    CELL_MORPHOLOGY = 'cell morphology'
    CELL_COUNTING = 'cell counting'
    CELL_POPULATION_CHARACTERIZATION = 'cell population characterization'
    COMPUTATIONAL_MODELING = 'computational modeling'


class DatasetType(str, Enum):
    GENERAL = 'GENERAL'
    BIDS = 'BIDS'


class DatasetCreationSchema(BaseSchema):
    """Dataset schema with creation fields."""

    code: constr(regex=settings.DATASET_CODE_REGEX, strip_whitespace=True)
    total_files: int = 0
    size: int = 0
    source: str = ''
    creator: str


class DatasetUpdateSchema(BaseSchema):
    """Dataset schema with update fields."""

    title: constr(max_length=100)
    authors: List[constr(max_length=50)] = Field(max_items=10)
    type: DatasetType = DatasetType.GENERAL
    modality: List[Modality] = []
    collection_method: List[constr(max_length=20)] = Field(max_items=10, default=[])
    license: Optional[constr(max_length=20)] = ''
    tags: List[constr(max_length=32)] = Field(max_items=10, default=[])
    description: constr(max_length=5000)

    @classmethod
    def from_schema(cls, schema_content: Dict[str, Any]) -> 'DatasetUpdateSchema':
        """Create an instance of DatasetUpdateSchema from SchemaDataset.content dict."""

        obj = {k.split('_')[1]: v for k, v in schema_content.items()}
        return cls(**obj)


class DatasetSchema(DatasetCreationSchema, DatasetUpdateSchema):
    """General dataset schema."""


class DatasetResponseSchema(DatasetSchema):
    """Default schema for single dataset in response."""

    id: UUID
    project_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DatasetListResponseSchema(ListResponseSchema):
    """Default schema for multiple datasets in response."""

    result: List[DatasetResponseSchema]
