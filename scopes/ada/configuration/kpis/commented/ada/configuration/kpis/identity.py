# Normaliza identidades KPI y destinos sin depender de identidades concretas de una Tool.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
import re

from ada.configuration.kpis.errors import KpiConfigurationValidationError

_KEY_PATTERN = re.compile(r'^[a-z0-9][a-z0-9._-]*$')


def require_identity_key(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if not _KEY_PATTERN.fullmatch(normalized):
        raise KpiConfigurationValidationError(f'{label} has an invalid format')
    return normalized
