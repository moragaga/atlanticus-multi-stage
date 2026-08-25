from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from time import monotonic
from types import MappingProxyType
from typing import Protocol

from .errors import DeliveryCacheConsistencyError, DeliveryCacheDefinitionError


# Latest y Timeseries son snapshots atómicos independientes y se protegen con locks distintos.
class DeliveryChannel(StrEnum):
    LATEST = 'latest'
    TIMESERIES = 'timeseries'


# El repository adapta el contrato externo a esta forma pequeña y serializable.
# La revisión identifica el snapshot; published_at_utc permite impedir retrocesos entre workers.
@dataclass(frozen=True, slots=True)
class DeliverySnapshot:
    revision: str
    published_at_utc: datetime
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'revision', _require_revision(self.revision))
        object.__setattr__(self, 'published_at_utc', _require_utc_datetime(self.published_at_utc))
        if not isinstance(self.payload, Mapping):
            raise DeliveryCacheDefinitionError('Delivery snapshot payload must be a mapping')
        normalized: dict[str, object] = {}
        for key, value in self.payload.items():
            if not isinstance(key, str) or not key:
                raise DeliveryCacheDefinitionError(
                    'Delivery snapshot payload keys must be non-empty strings'
                )
            # Se copia el payload recibido para que mutaciones posteriores del repository no alteren el cache.
            normalized[key] = deepcopy(value)
        object.__setattr__(self, 'payload', MappingProxyType(normalized))


# La conexión física queda fuera del cache. El repository usa la dependencia ya compuesta por Atlanticus.
class DeliveryRepository(Protocol):
    def read(self, channel: DeliveryChannel) -> DeliverySnapshot: ...


# Cada reemplazo publica una referencia completa para evitar snapshots parciales entre threads.
@dataclass(frozen=True, slots=True)
class _CacheValue:
    snapshot: DeliverySnapshot | None = None
    checked_at: float = -math.inf


# El lock pertenece exclusivamente a este proceso y a este canal.
@dataclass(slots=True)
class _CacheEntry:
    value: _CacheValue = field(default_factory=_CacheValue)
    lock: Lock = field(default_factory=Lock)


class WorkerDeliveryCache:
    def __init__(
        self,
        repository: DeliveryRepository,
        *,
        ttl_seconds: float = 1.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int | float):
            raise DeliveryCacheDefinitionError('Delivery cache ttl_seconds must be numeric')
        ttl_seconds = float(ttl_seconds)
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise DeliveryCacheDefinitionError(
                'Delivery cache ttl_seconds must be greater than zero'
            )
        if not callable(clock):
            raise DeliveryCacheDefinitionError('Delivery cache clock must be callable')
        if not hasattr(repository, 'read') or not callable(repository.read):
            raise DeliveryCacheDefinitionError('Delivery cache repository must provide read()')
        self._repository = repository
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries = {channel: _CacheEntry() for channel in DeliveryChannel}

    def read(self, channel: DeliveryChannel) -> DeliverySnapshot | None:
        channel = _require_channel(channel)
        entry = self._entries[channel]
        now = self._clock()
        value = entry.value
        # Dentro del TTL todos los usuarios y threads reutilizan la misma fotografía del proceso.
        if self._is_fresh(value, now):
            return value.snapshot
        # Single-flight no bloqueante: sólo un thread consulta; los demás usan last-known-good.
        if not entry.lock.acquire(blocking=False):
            return value.snapshot
        try:
            # Un thread previo pudo completar el refresh antes de adquirir el lock.
            now = self._clock()
            value = entry.value
            if self._is_fresh(value, now):
                return value.snapshot
            try:
                # Una única lectura obtiene revisión, fecha y payload del delivery atómico.
                incoming = self._repository.read(channel)
                incoming = _require_snapshot(incoming)
                snapshot = self._resolve_snapshot(value.snapshot, incoming)
            except Exception:
                # Con una fotografía válida previa se mantiene servicio y el TTL limita nuevos reintentos.
                if value.snapshot is None:
                    raise
                entry.value = _CacheValue(snapshot=value.snapshot, checked_at=self._clock())
                return value.snapshot
            entry.value = _CacheValue(snapshot=snapshot, checked_at=self._clock())
            return snapshot
        finally:
            entry.lock.release()

    def clear(self, channel: DeliveryChannel | None = None) -> None:
        # El clear afecta sólo memoria de este proceso; nunca modifica repository ni base de datos.
        if channel is None:
            for entry in self._entries.values():
                with entry.lock:
                    entry.value = _CacheValue()
            return
        entry = self._entries[_require_channel(channel)]
        with entry.lock:
            entry.value = _CacheValue()

    def _is_fresh(self, value: _CacheValue, now: float) -> bool:
        return value.snapshot is not None and now - value.checked_at < self._ttl_seconds

    @staticmethod
    def _resolve_snapshot(
        cached: DeliverySnapshot | None,
        incoming: DeliverySnapshot,
    ) -> DeliverySnapshot:
        if cached is None:
            return incoming
        # La revisión es la identidad: una misma revisión no puede cambiar su payload.
        if incoming.revision == cached.revision:
            if incoming.payload != cached.payload:
                raise DeliveryCacheConsistencyError(
                    'Delivery payload changed without changing its revision'
                )
            # Una lectura temporalmente más antigua nunca reemplaza el last-known-good.
            if incoming.published_at_utc < cached.published_at_utc:
                return cached
            return incoming
        # published_at_utc no detecta cambios; sólo protege contra retroceso entre workers.
        if incoming.published_at_utc < cached.published_at_utc:
            return cached
        if incoming.published_at_utc == cached.published_at_utc:
            raise DeliveryCacheConsistencyError(
                'Different delivery revisions cannot share the same publication time'
            )
        return incoming


def _require_channel(value: DeliveryChannel) -> DeliveryChannel:
    if not isinstance(value, DeliveryChannel):
        raise DeliveryCacheDefinitionError(f'Invalid delivery channel: {value!r}')
    return value


def _require_snapshot(value: DeliverySnapshot) -> DeliverySnapshot:
    if not isinstance(value, DeliverySnapshot):
        raise DeliveryCacheConsistencyError(
            'Delivery cache repository must return DeliverySnapshot instances'
        )
    return value


def _require_revision(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DeliveryCacheDefinitionError('Delivery snapshot revision must be a non-empty string')
    return value.strip()


def _require_utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DeliveryCacheDefinitionError(
            'Delivery snapshot published_at_utc must be timezone-aware'
        )
    if value.utcoffset().total_seconds() != 0:
        raise DeliveryCacheDefinitionError('Delivery snapshot published_at_utc must use UTC')
    return value.astimezone(UTC)
