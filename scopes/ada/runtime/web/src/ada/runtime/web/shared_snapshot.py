from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from time import monotonic
from types import MappingProxyType
from typing import Protocol

from .errors import RuntimeDefinitionError, SharedSnapshotConsistencyError

_TOOL_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_REVISION_PATTERN = re.compile(r'^\d{20}$')
_REVISION_FORMAT = '%Y%m%d%H%M%S%f'


class SnapshotChannel(StrEnum):
    DATA = 'data'
    TIME_SERIES = 'time_series'
    STATUS = 'status'


@dataclass(frozen=True, slots=True)
class SharedSnapshot:
    revision: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'revision', _require_revision(self.revision))
        if not isinstance(self.payload, Mapping):
            raise RuntimeDefinitionError('Shared snapshot payload must be a mapping')
        normalized: dict[str, object] = {}
        for key, value in self.payload.items():
            if not isinstance(key, str) or not key:
                raise RuntimeDefinitionError(
                    'Shared snapshot payload keys must be non-empty strings'
                )
            normalized[key] = value
        object.__setattr__(self, 'payload', MappingProxyType(normalized))


class SnapshotRepository(Protocol):
    def read_revision(self, tool_key: str, channel: SnapshotChannel) -> str: ...

    def read_snapshot(self, tool_key: str, channel: SnapshotChannel) -> SharedSnapshot: ...


@dataclass(frozen=True, slots=True)
class _CacheValue:
    revision: str | None = None
    snapshot: SharedSnapshot | None = None
    checked_at: float = -math.inf


@dataclass(slots=True)
class _CacheEntry:
    value: _CacheValue = field(default_factory=_CacheValue)
    lock: Lock = field(default_factory=Lock)


class SharedSnapshotReader:
    def __init__(
        self,
        repository: SnapshotRepository,
        *,
        ttl_seconds: float = 1.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int | float):
            raise RuntimeDefinitionError('Shared snapshot cache ttl_seconds must be numeric')
        ttl_seconds = float(ttl_seconds)
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise RuntimeDefinitionError(
                'Shared snapshot cache ttl_seconds must be greater than zero'
            )
        if not callable(clock):
            raise RuntimeDefinitionError('Shared snapshot cache clock must be callable')
        self._repository = repository
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: dict[tuple[str, SnapshotChannel], _CacheEntry] = {}
        self._entries_lock = Lock()

    def read(
        self,
        tool_key: str,
        channel: SnapshotChannel,
        *,
        client_revision: str | None = None,
    ) -> SharedSnapshot | None:
        tool_key = _require_tool_key(tool_key)
        if not isinstance(channel, SnapshotChannel):
            raise RuntimeDefinitionError(f'Invalid shared snapshot channel: {channel!r}')
        if client_revision is not None:
            client_revision = _require_revision(client_revision)

        entry = self._entry(tool_key, channel)
        value = entry.value
        fast = self._fast_result(value, client_revision, self._clock())
        if fast is not _REVALIDATE:
            return fast

        with entry.lock:
            value = entry.value
            now = self._clock()
            fast = self._fast_result(value, client_revision, now)
            if fast is not _REVALIDATE:
                return fast

            if self._is_fresh(value, now) and value.revision is not None and value.snapshot is None:
                snapshot = self._load_snapshot(tool_key, channel, value.revision)
                entry.value = _CacheValue(
                    revision=snapshot.revision,
                    snapshot=snapshot,
                    checked_at=self._clock(),
                )
                return self._result(snapshot, client_revision)

            shared_revision = self._read_revision(tool_key, channel)

            if client_revision is not None and client_revision > shared_revision:
                return None

            if value.revision is not None and value.revision > shared_revision:
                if value.snapshot is None:
                    if client_revision is not None:
                        return None
                    raise SharedSnapshotConsistencyError(
                        'Shared repository revision is older than the latest revision cached by this worker'
                    )
                return self._result(value.snapshot, client_revision)

            if value.revision == shared_revision:
                refreshed = _CacheValue(
                    revision=value.revision,
                    snapshot=value.snapshot,
                    checked_at=self._clock(),
                )
                entry.value = refreshed
                if refreshed.snapshot is None:
                    if client_revision == shared_revision:
                        return None
                    snapshot = self._load_snapshot(tool_key, channel, shared_revision)
                    entry.value = _CacheValue(
                        revision=snapshot.revision,
                        snapshot=snapshot,
                        checked_at=self._clock(),
                    )
                    return self._result(snapshot, client_revision)
                return self._result(refreshed.snapshot, client_revision)

            if client_revision == shared_revision:
                entry.value = _CacheValue(
                    revision=shared_revision,
                    snapshot=None,
                    checked_at=self._clock(),
                )
                return None

            snapshot = self._load_snapshot(tool_key, channel, shared_revision)
            entry.value = _CacheValue(
                revision=snapshot.revision,
                snapshot=snapshot,
                checked_at=self._clock(),
            )
            return self._result(snapshot, client_revision)

    def clear(self) -> None:
        with self._entries_lock:
            self._entries = {}

    def _entry(self, tool_key: str, channel: SnapshotChannel) -> _CacheEntry:
        key = (tool_key, channel)
        entry = self._entries.get(key)
        if entry is not None:
            return entry
        with self._entries_lock:
            return self._entries.setdefault(key, _CacheEntry())

    def _fast_result(
        self,
        value: _CacheValue,
        client_revision: str | None,
        now: float,
    ) -> SharedSnapshot | None | object:
        if not self._is_fresh(value, now) or value.revision is None:
            return _REVALIDATE
        if client_revision == value.revision:
            return None
        if client_revision is not None and client_revision > value.revision:
            return _REVALIDATE
        if value.snapshot is None:
            return _REVALIDATE
        return value.snapshot

    def _is_fresh(self, value: _CacheValue, now: float) -> bool:
        return now - value.checked_at < self._ttl_seconds

    def _read_revision(self, tool_key: str, channel: SnapshotChannel) -> str:
        return _require_revision(self._repository.read_revision(tool_key, channel))

    def _load_snapshot(
        self,
        tool_key: str,
        channel: SnapshotChannel,
        advertised_revision: str,
    ) -> SharedSnapshot:
        snapshot = self._repository.read_snapshot(tool_key, channel)
        if not isinstance(snapshot, SharedSnapshot):
            raise SharedSnapshotConsistencyError(
                'Shared snapshot repository must return SharedSnapshot instances'
            )
        if snapshot.revision == advertised_revision:
            return snapshot

        confirmed_revision = self._read_revision(tool_key, channel)
        if confirmed_revision < advertised_revision or snapshot.revision != confirmed_revision:
            raise SharedSnapshotConsistencyError(
                'Shared snapshot revision does not match the repository revision'
            )
        return snapshot

    @staticmethod
    def _result(
        snapshot: SharedSnapshot,
        client_revision: str | None,
    ) -> SharedSnapshot | None:
        if client_revision == snapshot.revision:
            return None
        if client_revision is not None and client_revision > snapshot.revision:
            return None
        return snapshot


_REVALIDATE = object()


def snapshot_revision_datetime_utc(value: str) -> datetime:
    normalized = _require_revision(value)
    return datetime.strptime(normalized, _REVISION_FORMAT).replace(tzinfo=UTC)


def _require_revision(value: str) -> str:
    if not isinstance(value, str) or not _REVISION_PATTERN.fullmatch(value):
        raise RuntimeDefinitionError(
            'Shared snapshot revision must use UTC format YYYYMMDDHHMMSSffffff'
        )
    try:
        datetime.strptime(value, _REVISION_FORMAT)
    except ValueError as error:
        raise RuntimeDefinitionError(
            'Shared snapshot revision must contain a valid UTC date and time'
        ) from error
    return value


def _require_tool_key(value: str) -> str:
    if not isinstance(value, str) or not _TOOL_KEY_PATTERN.fullmatch(value):
        raise RuntimeDefinitionError(f'Invalid tool key: {value!r}')
    return value
