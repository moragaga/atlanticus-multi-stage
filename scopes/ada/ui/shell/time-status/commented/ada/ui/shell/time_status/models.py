# Contratos inmutables que mantienen estable la estructura visual de Time Status.
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ada.contracts.tool_manifest import ToolSourceKey
from ada.runtime.web import SourceState

TIME_STATUS_TIMEZONE = 'America/Santiago'


@dataclass(frozen=True, slots=True)
class TimeStatusSourceState:
    key: ToolSourceKey
    label: str
    stale_after_seconds: int
    runtime_state: SourceState

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError('Time status source label cannot be empty')
        if isinstance(self.stale_after_seconds, bool) or not isinstance(
            self.stale_after_seconds,
            int,
        ):
            raise ValueError('Time status stale_after_seconds must be an integer')
        if self.stale_after_seconds <= 0:
            raise ValueError('Time status stale_after_seconds must be greater than zero')
        if self.runtime_state.key != self.key.value:
            raise ValueError('Time status source key does not match runtime state')

    @property
    def updated_at_utc(self) -> datetime | None:
        return self.runtime_state.updated_at_utc


@dataclass(frozen=True, slots=True)
class TimeStatusState:
    tool_key: str
    sources: tuple[TimeStatusSourceState, ...]
    timezone: str = TIME_STATUS_TIMEZONE

    def __post_init__(self) -> None:
        if not self.tool_key.strip():
            raise ValueError('Time status tool_key cannot be empty')
        object.__setattr__(self, 'sources', tuple(self.sources))
        if not self.sources:
            raise ValueError('Time status requires at least one source')
        keys = [source.key for source in self.sources]
        if len(keys) != len(set(keys)):
            raise ValueError('Time status contains duplicate source keys')
        if ToolSourceKey.PI not in keys:
            raise ValueError('Time status requires the pi source')
        if not self.timezone.strip():
            raise ValueError('Time status timezone cannot be empty')
