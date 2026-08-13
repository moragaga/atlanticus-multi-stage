# Espejo comentado del cache por worker y refresh coordinado.
# Mantiene el mismo AST que la implementación productiva.
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock

from .gate import Gate
from .snapshot import RuntimeDefinition, RuntimeSnapshot

SnapshotLoader = Callable[[], RuntimeSnapshot]
MonotonicClock = Callable[[], float]
UtcClock = Callable[[], datetime]


class RefreshState(StrEnum):
    UPDATED = 'updated'
    UNCHANGED = 'unchanged'
    BUSY = 'busy'
    NOT_DUE = 'not_due'


@dataclass(frozen=True, slots=True)
class RuntimeView:
    version: int
    snapshot: RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class RefreshResult:
    state: RefreshState
    version: int
    revision: str
    error_type: str | None = None


class AdaRuntime:
    """Per-worker runtime cache with atomic snapshots and non-blocking refresh."""

    def __init__(
        self,
        *,
        shape: RuntimeDefinition,
        loader: SnapshotLoader,
        refresh_interval_seconds: float,
        monotonic: MonotonicClock = time.monotonic,
        utcnow: UtcClock | None = None,
    ) -> None:
        if refresh_interval_seconds <= 0:
            raise ValueError('refresh_interval_seconds must be greater than zero')
        self._shape = shape
        self._loader = loader
        self._refresh_interval_seconds = float(refresh_interval_seconds)
        self._monotonic = monotonic
        self._utcnow = utcnow or (lambda: datetime.now(UTC))
        self._gate = Gate()
        self._state_lock = RLock()
        self._snapshot = shape.bootstrap(loaded_at_utc=self._utcnow())
        self._version = 0
        self._next_refresh_at = 0.0

    def current(self) -> RuntimeView:
        with self._state_lock:
            return RuntimeView(version=self._version, snapshot=self._snapshot)

    def warmup(self) -> RefreshResult:
        return self.refresh(force=True)

    def refresh_if_due(self) -> RefreshResult:
        return self.refresh(force=False)

    def refresh(self, *, force: bool = False) -> RefreshResult:
        now = self._monotonic()
        if not force and not self._is_due(now):
            return self._result(RefreshState.NOT_DUE)

        with self._gate.enter() as entered:
            if not entered:
                return self._result(RefreshState.BUSY)

            now = self._monotonic()
            if not force and not self._is_due(now):
                return self._result(RefreshState.NOT_DUE)

            candidate, error_type = self._load_safe()
            normalized = self._shape.normalize(candidate)
            with self._state_lock:
                changed = (
                    normalized.revision != self._snapshot.revision
                    or normalized.sources != self._snapshot.sources
                )
                if changed:
                    self._snapshot = normalized
                    self._version += 1
                self._next_refresh_at = self._monotonic() + self._refresh_interval_seconds
                state = RefreshState.UPDATED if changed else RefreshState.UNCHANGED
                return RefreshResult(
                    state=state,
                    version=self._version,
                    revision=self._snapshot.revision,
                    error_type=error_type,
                )

    @property
    def refresh_busy(self) -> bool:
        return self._gate.busy

    def _load_safe(self) -> tuple[RuntimeSnapshot, str | None]:
        try:
            snapshot = self._loader()
            if not isinstance(snapshot, RuntimeSnapshot):
                raise TypeError('Runtime loader must return RuntimeSnapshot')
            return snapshot, None
        except Exception as error:  # Boundary intentionally contains source failures.
            error_type = type(error).__name__
            return (
                self._shape.failure(
                    error_type=error_type,
                    loaded_at_utc=self._utcnow(),
                ),
                error_type,
            )

    def _is_due(self, now: float) -> bool:
        with self._state_lock:
            return now >= self._next_refresh_at

    def _result(self, state: RefreshState) -> RefreshResult:
        current = self.current()
        return RefreshResult(
            state=state,
            version=current.version,
            revision=current.snapshot.revision,
        )
