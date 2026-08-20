# Interpreta el ambiente y el bypass administrativo operacional desde variables ya inyectadas por deployment.
from __future__ import annotations

import re

from atlanticus.web.environment import EnvironmentReader, WebEnvironment, resolve_environment
from atlanticus.web.errors import WebConfigurationError

_ENVIRONMENT_VARIABLE = 'ATLANTICUS_ENVIRONMENT'
_BOOTSTRAP_ADMIN_VARIABLE = 'ATLANTICUS_BOOTSTRAP_ADMIN'
_EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+$')


def resolve_deployment_environment(reader: EnvironmentReader) -> WebEnvironment:
    if not isinstance(reader, EnvironmentReader):
        raise TypeError('reader must be EnvironmentReader')
    value = reader.optional(_ENVIRONMENT_VARIABLE)
    values = {} if value is None else {_ENVIRONMENT_VARIABLE: value}
    return resolve_environment(values)


def resolve_bootstrap_admin_principal(
    reader: EnvironmentReader,
    environment: WebEnvironment,
) -> str | None:
    if not isinstance(reader, EnvironmentReader):
        raise TypeError('reader must be EnvironmentReader')
    if not isinstance(environment, WebEnvironment):
        raise TypeError('environment must be WebEnvironment')
    if environment.is_local:
        return None

    value = reader.optional(_BOOTSTRAP_ADMIN_VARIABLE)
    if value is None or value.casefold() == 'off':
        return None
    if value != value.strip() or not _EMAIL_PATTERN.fullmatch(value):
        raise WebConfigurationError(
            f'Invalid {_BOOTSTRAP_ADMIN_VARIABLE}: expected off or an email address'
        )
    return value.casefold()
