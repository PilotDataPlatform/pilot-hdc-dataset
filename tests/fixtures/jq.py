# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Iterable
from typing import Any

import httpx
import jq as json_processor
import pytest
import requests


class JQResult:
    def __init__(self, result: Any) -> None:
        self.result = result

    def all(self, to: type = list, each_to: type = None) -> Iterable[Any]:
        """Retrieve all values, optionally casting each item to a specified type and the entire list to another type."""

        values = self.result.all()

        if each_to is not None:
            values = map(each_to, values)

        return to(values)

    def first(self, to: type | None = None) -> Any:
        """Retrieve first value, optionally casting it to a desired type."""

        value = self.result.first()

        if to is not None:
            value = to(value)

        return value


class JQ:
    """Perform jq queries against common client responses or JSON structured data."""

    def __init__(self, value: httpx.Response | requests.Response | dict[str, Any]) -> None:
        if isinstance(value, (httpx.Response, requests.Response)):
            value = value.json()

        self.value = value

    def __call__(self, query: str) -> JQResult:
        return JQResult(json_processor.compile(query).input(self.value))


@pytest.fixture
def jq() -> type[JQ]:
    return JQ
