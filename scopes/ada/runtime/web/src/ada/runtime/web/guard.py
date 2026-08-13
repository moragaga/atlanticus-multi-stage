from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .snapshot import Freshness, RuntimeSnapshot, SourceHealth


class GuardState(StrEnum):
    READY = 'ready'
    CONSTRUCTION = 'construction'
    STALE = 'stale'
    SOURCE_ERROR = 'source_error'
    COMPONENT_ERROR = 'component_error'


@dataclass(frozen=True, slots=True)
class GuardResult:
    state: GuardState
    affected_sources: tuple[str, ...] = ()


def resolve_guard(
    snapshot: RuntimeSnapshot,
    *,
    required_sources: tuple[str, ...] = (),
    construction: bool = False,
    component_error: bool = False,
) -> GuardResult:
    if construction:
        return GuardResult(GuardState.CONSTRUCTION)
    if component_error:
        return GuardResult(GuardState.COMPONENT_ERROR)

    sources = tuple(snapshot.source(key) for key in required_sources)
    unhealthy = tuple(source.key for source in sources if source.health is not SourceHealth.HEALTHY)
    if unhealthy:
        return GuardResult(GuardState.SOURCE_ERROR, unhealthy)

    stale = tuple(source.key for source in sources if source.freshness is Freshness.STALE)
    if stale:
        return GuardResult(GuardState.STALE, stale)

    return GuardResult(GuardState.READY)
