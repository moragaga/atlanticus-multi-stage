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


class DeliveryChannel(StrEnum):
    LATEST = 'latest'
    TIMESERIES = 'timeseries'


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
            normalized[key] = deepcopy(value)
        object.__setattr__(self, 'payload', MappingProxyType(normalized))


class DeliveryRepository(Protocol):
    def read(self, channel: DeliveryChannel) -> DeliverySnapshot: ...


@dataclass(frozen=True, slots=True)
class _CacheValue:
    snapshot: DeliverySnapshot | None = None
    checked_at: float = -math.inf


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
        if self._is_fresh(value, now):
            return value.snapshot
        if not entry.lock.acquire(blocking=False):
            return value.snapshot
        try:
            now = self._clock()
            value = entry.value
            if self._is_fresh(value, now):
                return value.snapshot
            try:
                incoming = self._repository.read(channel)
                incoming = _require_snapshot(incoming)
                snapshot = self._resolve_snapshot(value.snapshot, incoming)
            except Exception:
                if value.snapshot is None:
                    raise
                entry.value = _CacheValue(snapshot=value.snapshot, checked_at=self._clock())
                return value.snapshot
            entry.value = _CacheValue(snapshot=snapshot, checked_at=self._clock())
            return snapshot
        finally:
            entry.lock.release()

    def clear(self, channel: DeliveryChannel | None = None) -> None:
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
        if incoming.revision == cached.revision:
            if incoming.payload != cached.payload:
                raise DeliveryCacheConsistencyError(
                    'Delivery payload changed without changing its revision'
                )
            if incoming.published_at_utc < cached.published_at_utc:
                return cached
            return incoming
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
