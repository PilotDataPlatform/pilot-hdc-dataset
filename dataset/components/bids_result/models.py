# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy import JSON
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TIMESTAMP

from dataset.components.models import DBModel


class BIDSResult(DBModel):
    __tablename__ = 'bids_results'
    __table_args__ = (UniqueConstraint('dataset_code', name='bids_results_dataset_code_unique'),)

    id = Column(Integer, primary_key=True)
    dataset_code = Column(String(), unique=True)
    created_time = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    updated_time = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    validate_output = Column(JSON())
