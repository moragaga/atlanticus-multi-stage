# Estado de señal y lock por sesión para impedir refresh Dash encolados.
from __future__ import annotations

from datetime import UTC, datetime
from typing import Mapping
from uuid import uuid4

from .errors import RuntimeDeliveryCollectorError

DEFAULT_REFRESH_LOCK_TTL_SECONDS = 90.0


# Crea una señal única para una nueva ejecución permitida de la sesión.
def build_refresh_signal(*, now: datetime | None = None) -> dict[str, object]:
    instant = _utc_now(now)
    return {
        'token': str(uuid4()),
        'created_at_utc': _to_iso(instant),
    }


# Marca la sesión como ocupada usando el token de la señal activa.
def build_acquired_refresh_lock(
    signal: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    token = _require_token(signal.get('token'))
    instant = _utc_now(now)
    return {
        'is_running': True,
        'active_token': token,
        'started_at_utc': _to_iso(instant),
    }


# Devuelve el lock a estado libre una vez finaliza el Collector.
def build_released_refresh_lock(*, now: datetime | None = None) -> dict[str, object]:
    instant = _utc_now(now)
    return {
        'is_running': False,
        'active_token': None,
        'started_at_utc': None,
        'released_at_utc': _to_iso(instant),
    }


# Permite recuperación si una ejecución quedó trabada más allá del TTL.
def is_refresh_lock_expired(
    lock_data: Mapping[str, object] | None,
    *,
    ttl_seconds: float = DEFAULT_REFRESH_LOCK_TTL_SECONDS,
    now: datetime | None = None,
) -> bool:
    if not lock_data or not bool(lock_data.get('is_running', False)):
        return False
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int | float):
        raise RuntimeDeliveryCollectorError('Refresh lock ttl_seconds must be numeric')
    ttl = float(ttl_seconds)
    if ttl <= 0:
        raise RuntimeDeliveryCollectorError('Refresh lock ttl_seconds must be greater than zero')
    started = _parse_iso(lock_data.get('started_at_utc'))
    if started is None:
        return True
    return (_utc_now(now) - started).total_seconds() > ttl


def _require_token(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeDeliveryCollectorError('Refresh signal token must be a non-empty string')
    return value.strip()


def _utc_now(value: datetime | None) -> datetime:
    instant = value or datetime.now(tz=UTC)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise RuntimeDeliveryCollectorError('Refresh timestamp must be timezone-aware')
    return instant.astimezone(UTC)


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(UTC)


def _to_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')
