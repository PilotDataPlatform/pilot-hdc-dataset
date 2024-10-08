# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from dataset.components.bids_result.models import BIDSResult
from dataset.components.bids_result.schemas import UpdateBIDSResultSchema
from dataset.components.crud import CRUD


class BIDSResultCRUD(CRUD):
    """CRUD for managing BIDS result database models."""

    model = BIDSResult

    async def retrieve_by_dataset_code(self, dataset_code: str) -> BIDSResult:
        """Get last created BIDS result by unique dataset code."""

        statement = (
            select(self.model).where(self.model.dataset_code == dataset_code).order_by(BIDSResult.created_time.desc())
        )
        dataset = await self._retrieve_one(statement)
        return dataset

    async def create_or_update_result(self, dataset_code: str, bids_output: UpdateBIDSResultSchema) -> BIDSResult:
        """Create the BIDS result in the table if the dataset code does not existed, otherwise update the result."""

        insert_bids = insert(self.model).values(
            dataset_code=dataset_code,
            validate_output=bids_output.validate_output,
        )

        do_update_bids = insert_bids.on_conflict_do_update(
            index_elements=[BIDSResult.dataset_code],
            set_={self.model.validate_output: bids_output.validate_output},
            where=(self.model.dataset_code == dataset_code),
        )

        await self.execute(do_update_bids)

        dataset = await self.retrieve_by_dataset_code(dataset_code)
        return dataset
