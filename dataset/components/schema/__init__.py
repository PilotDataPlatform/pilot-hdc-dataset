# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from dataset.components.schema.models import SchemaDataset
from dataset.components.schema.views import router as schema_router

__all__ = [
    'SchemaDataset',
    'schema_router',
]
