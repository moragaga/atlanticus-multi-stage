from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .errors import RuntimeDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_.-]*$')


class SourceHealth(StrEnum):
    HEALTHY = 'healthy'
    UNAVAILABLE = 'unavailable'
    INVALID = 'invalid'
    ERROR = 'error'


class Freshness(StrEnum):
    FRESH = 'fresh'
    STALE = 'stale'
    UNKNOWN = 'unknown'


class ValueStatus(StrEnum):
    OK = 'ok'
    NOT_MAPPED = 'not_mapped'
    EMPTY = 'empty'
    INVALID = 'invalid'
    ERROR = 'error'


@dataclass(frozen=True, slots=True)
class SourceState:
    key: str
    health: SourceHealth
    freshness: Freshness = Freshness.UNKNOWN
    updated_at_utc: datetime | None = None

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='source key')
        if self.updated_at_utc is not None:
            object.__setattr__(self, 'updated_at_utc', _as_utc(self.updated_at_utc))
        if self.health is SourceHealth.HEALTHY:
            if self.updated_at_utc is None:
                raise RuntimeDefinitionError('Healthy source requires updated_at_utc')
            if self.freshness is Freshness.UNKNOWN:
                raise RuntimeDefinitionError('Healthy source requires known freshness')
        elif self.freshness is not Freshness.UNKNOWN:
            raise RuntimeDefinitionError('Unhealthy source freshness must be unknown')

    @classmethod
    def healthy(
        cls,
        key: str,
        *,
        updated_at_utc: datetime,
        stale: bool = False,
    ) -> SourceState:
        return cls(
            key=key,
            health=SourceHealth.HEALTHY,
            freshness=Freshness.STALE if stale else Freshness.FRESH,
            updated_at_utc=updated_at_utc,
        )

    @classmethod
    def unavailable(
        cls,
        key: str,
        *,
        updated_at_utc: datetime | None = None,
    ) -> SourceState:
        return cls(
            key=key,
            health=SourceHealth.UNAVAILABLE,
            updated_at_utc=updated_at_utc,
        )

    @classmethod
    def invalid(
        cls,
        key: str,
        *,
        updated_at_utc: datetime | None = None,
    ) -> SourceState:
        return cls(
            key=key,
            health=SourceHealth.INVALID,
            updated_at_utc=updated_at_utc,
        )

    @classmethod
    def error(
        cls,
        key: str,
        *,
        updated_at_utc: datetime | None = None,
    ) -> SourceState:
        return cls(
            key=key,
            health=SourceHealth.ERROR,
            updated_at_utc=updated_at_utc,
        )


@dataclass(frozen=True, slots=True)
class ValueState:
    key: str
    status: ValueStatus
    value: object | None = None

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='value key')
        if self.status is ValueStatus.OK and self.value is None:
            raise RuntimeDefinitionError('OK value requires a concrete value')
        if self.status is not ValueStatus.OK and self.value is not None:
            raise RuntimeDefinitionError('Degraded value cannot expose a fallback value')

    @classmethod
    def ok(cls, key: str, value: object) -> ValueState:
        return cls(key=key, status=ValueStatus.OK, value=value)

    @classmethod
    def not_mapped(cls, key: str) -> ValueState:
        return cls(key=key, status=ValueStatus.NOT_MAPPED)

    @classmethod
    def empty(cls, key: str) -> ValueState:
        return cls(key=key, status=ValueStatus.EMPTY)

    @classmethod
    def invalid(cls, key: str) -> ValueState:
        return cls(key=key, status=ValueStatus.INVALID)

    @classmethod
    def error(cls, key: str) -> ValueState:
        return cls(key=key, status=ValueStatus.ERROR)


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    revision: str
    loaded_at_utc: datetime
    sources: Mapping[str, SourceState] = field(default_factory=dict)
    values: Mapping[str, ValueState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        revision = self.revision.strip()
        if not revision:
            raise RuntimeDefinitionError('Runtime snapshot revision cannot be empty')
        object.__setattr__(self, 'revision', revision)
        object.__setattr__(self, 'loaded_at_utc', _as_utc(self.loaded_at_utc))
        object.__setattr__(self, 'sources', _freeze_states(self.sources, SourceState, 'source'))
        object.__setattr__(self, 'values', _freeze_states(self.values, ValueState, 'value'))

    def source(self, key: str) -> SourceState:
        normalized = _normalized_key(key, field_name='source key')
        return self.sources.get(normalized, SourceState.unavailable(normalized))

    def value(self, key: str) -> ValueState:
        normalized = _normalized_key(key, field_name='value key')
        return self.values.get(normalized, ValueState.not_mapped(normalized))


@dataclass(frozen=True, slots=True)
class RuntimeSourceDefinition:
    key: str
    stale_after_seconds: int

    def __post_init__(self) -> None:
        _require_key(self.key, field_name='source key')
        if isinstance(self.stale_after_seconds, bool) or not isinstance(
            self.stale_after_seconds, int
        ):
            raise RuntimeDefinitionError('Source stale_after_seconds must be an integer')
        if self.stale_after_seconds <= 0:
            raise RuntimeDefinitionError('Source stale_after_seconds must be greater than zero')

    def normalize(
        self,
        state: SourceState,
        *,
        evaluated_at_utc: datetime,
    ) -> SourceState:
        if state.health is not SourceHealth.HEALTHY:
            return state
        age_seconds = (evaluated_at_utc - state.updated_at_utc).total_seconds()
        freshness = Freshness.STALE if age_seconds >= self.stale_after_seconds else Freshness.FRESH
        return SourceState(
            key=state.key,
            health=state.health,
            freshness=freshness,
            updated_at_utc=state.updated_at_utc,
        )


@dataclass(frozen=True, slots=True)
class RuntimeDefinition:
    sources: tuple[RuntimeSourceDefinition, ...] = ()
    value_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, 'sources', _unique_source_definitions(self.sources))
        object.__setattr__(self, 'value_keys', _unique_keys(self.value_keys, 'value key'))

    def normalize(
        self,
        snapshot: RuntimeSnapshot,
        *,
        evaluated_at_utc: datetime,
    ) -> RuntimeSnapshot:
        evaluated_at_utc = _as_utc(evaluated_at_utc)
        sources: dict[str, SourceState] = {}
        values = dict(snapshot.values)
        for definition in self.sources:
            state = snapshot.sources.get(
                definition.key,
                SourceState.unavailable(definition.key),
            )
            sources[definition.key] = definition.normalize(
                state,
                evaluated_at_utc=evaluated_at_utc,
            )
        for key in self.value_keys:
            values.setdefault(key, ValueState.not_mapped(key))
        return RuntimeSnapshot(
            revision=snapshot.revision,
            loaded_at_utc=snapshot.loaded_at_utc,
            sources=sources,
            values=values,
        )

    def bootstrap(self, *, loaded_at_utc: datetime) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            revision='bootstrap',
            loaded_at_utc=loaded_at_utc,
            sources={
                definition.key: SourceState.unavailable(definition.key)
                for definition in self.sources
            },
            values={key: ValueState.not_mapped(key) for key in self.value_keys},
        )

    def failure(
        self,
        *,
        error_type: str,
        loaded_at_utc: datetime,
    ) -> RuntimeSnapshot:
        normalized_error = error_type.strip() or 'RuntimeError'
        return RuntimeSnapshot(
            revision=f'runtime-error:{normalized_error}',
            loaded_at_utc=loaded_at_utc,
            sources={
                definition.key: SourceState.error(definition.key) for definition in self.sources
            },
            values={key: ValueState.error(key) for key in self.value_keys},
        )


def _freeze_states(
    values: Mapping[str, object],
    expected_type: type,
    label: str,
) -> Mapping[str, object]:
    normalized: dict[str, object] = {}
    for raw_key, state in values.items():
        key = _normalized_key(raw_key, field_name=f'{label} mapping key')
        if not isinstance(state, expected_type):
            raise RuntimeDefinitionError(f'Invalid {label} state for {key!r}')
        if state.key != key:
            raise RuntimeDefinitionError(f'{label.title()} state key does not match mapping key')
        normalized[key] = state
    return MappingProxyType(normalized)


def _unique_source_definitions(
    values: tuple[RuntimeSourceDefinition, ...],
) -> tuple[RuntimeSourceDefinition, ...]:
    normalized = tuple(values)
    if not all(isinstance(value, RuntimeSourceDefinition) for value in normalized):
        raise RuntimeDefinitionError('Runtime sources must use RuntimeSourceDefinition')
    keys = [value.key for value in normalized]
    if len(keys) != len(set(keys)):
        raise RuntimeDefinitionError('Duplicate source keys are not allowed')
    return normalized


def _unique_keys(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_normalized_key(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        raise RuntimeDefinitionError(f'Duplicate {field_name}s are not allowed')
    return normalized


def _require_key(value: str, *, field_name: str) -> None:
    _normalized_key(value, field_name=field_name)


def _normalized_key(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not _KEY_PATTERN.fullmatch(normalized):
        raise RuntimeDefinitionError(f'Invalid {field_name}: {value!r}')
    return normalized


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise RuntimeDefinitionError('Runtime timestamps must be timezone-aware')
    return value.astimezone(UTC)
