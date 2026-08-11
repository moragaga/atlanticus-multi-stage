from __future__ import annotations

import os
import re
from collections.abc import Mapping

from atlanticus.web.identity.errors import IdentityConfigurationError

IDENTITY_PROVIDER_ENV = 'ATLANTICUS_IDENTITY_PROVIDER'
_PROVIDER_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9._-]*$')


def resolve_identity_provider_key(environ: Mapping[str, str] | None = None) -> str:
    source = os.environ if environ is None else environ
    value = source.get(IDENTITY_PROVIDER_ENV)
    if value is None or not value.strip():
        raise IdentityConfigurationError(
            f'Missing required environment variable: {IDENTITY_PROVIDER_ENV}'
        )

    normalized = value.strip()
    if normalized != value or not _PROVIDER_KEY_PATTERN.fullmatch(normalized):
        raise IdentityConfigurationError(f'Invalid identity provider key: {value!r}')
    return normalized
