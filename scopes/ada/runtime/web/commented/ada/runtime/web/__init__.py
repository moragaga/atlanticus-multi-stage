# Superficie pública del runtime web, incluyendo las proyecciones por componente.

from .errors import RuntimeDefinitionError
from .gate import Gate
from .guard import GuardResult, GuardState, resolve_guard
from .projections import (
    ComponentDataSnapshot,
    ComponentProjectionState,
    ComponentStateSnapshot,
    ComponentTimeSeriesSnapshot,
    TimeSeriesWindowSnapshot,
)
from .runtime import AdaRuntime, RefreshResult, RefreshState, RuntimeView
from .snapshot import (
    Freshness,
    RuntimeDefinition,
    RuntimeSnapshot,
    RuntimeSourceDefinition,
    SourceHealth,
    SourceState,
    ValueState,
    ValueStatus,
)

__all__ = [
    'ComponentDataSnapshot',
    'ComponentProjectionState',
    'ComponentStateSnapshot',
    'ComponentTimeSeriesSnapshot',
    'AdaRuntime',
    'Freshness',
    'Gate',
    'GuardResult',
    'GuardState',
    'RefreshResult',
    'RefreshState',
    'RuntimeDefinitionError',
    'RuntimeDefinition',
    'RuntimeSnapshot',
    'RuntimeSourceDefinition',
    'RuntimeView',
    'SourceHealth',
    'SourceState',
    'TimeSeriesWindowSnapshot',
    'ValueState',
    'ValueStatus',
    'resolve_guard',
]
