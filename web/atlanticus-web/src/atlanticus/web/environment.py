from __future__ import annotations

import os
from collections.abc import Mapping
from enum import StrEnum

from atlanticus.web.errors import WebConfigurationError

_ENVIRONMENT_VARIABLE = 'ATLANTICUS_ENVIRONMENT'


class WebEnvironment(StrEnum):
    LOCAL = 'local'
    PRODUCTION = 'production'

    @property
    def is_local(self) -> bool:
        return self is WebEnvironment.LOCAL

    @property
    def is_production(self) -> bool:
        return self is WebEnvironment.PRODUCTION


def resolve_environment(values: Mapping[str, str] | None = None) -> WebEnvironment:
    source = os.environ if values is None else values
    raw_value = source.get(_ENVIRONMENT_VARIABLE, WebEnvironment.LOCAL.value)
    normalized = raw_value.strip().lower()

    try:
        return WebEnvironment(normalized)
    except ValueError as exc:
        raise WebConfigurationError(
            f'Invalid {_ENVIRONMENT_VARIABLE}: expected local or production'
        ) from exc
