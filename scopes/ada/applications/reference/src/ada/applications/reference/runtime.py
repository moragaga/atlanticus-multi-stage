from __future__ import annotations

from datetime import UTC, datetime

from ada.runtime.web import AdaRuntime, RuntimeDefinition, RuntimeSnapshot, SourceState, ValueState
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry

ADA_RUNTIME_SERVICE = 'ada.runtime'
REFERENCE_INDICATOR_KEYS = (
    'transportado',
    'molienda',
    'ley_cobre',
    'recuperacion_cu',
    'cu_fino_producido',
    'mo_fino_producido',
    'expit',
    'cu_fino_filtrado_pagable',
)


def create_reference_runtime_module() -> WebModule:
    return WebModule(
        name='ada-runtime',
        register_services=_register_runtime,
    )


def _register_runtime(services: ServiceRegistry) -> None:
    runtime = _build_runtime()
    runtime.warmup()
    services.add(ADA_RUNTIME_SERVICE, runtime)


def _build_runtime() -> AdaRuntime:
    shape = RuntimeDefinition(
        source_keys=('pi', 'dispatch'),
        value_keys=REFERENCE_INDICATOR_KEYS,
    )
    return AdaRuntime(
        shape=shape,
        loader=_load_reference_snapshot,
        refresh_interval_seconds=10,
    )


def _load_reference_snapshot() -> RuntimeSnapshot:
    now = datetime.now(UTC)
    return RuntimeSnapshot(
        revision='reference-2',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
        values={
            'transportado': ValueState.ok('transportado', '198'),
            'ley_cobre': ValueState.empty('ley_cobre'),
            'recuperacion_cu': ValueState.invalid('recuperacion_cu'),
            'cu_fino_producido': ValueState.error('cu_fino_producido'),
            'mo_fino_producido': ValueState.ok('mo_fino_producido', '28'),
            'expit': ValueState.ok('expit', '376'),
            'cu_fino_filtrado_pagable': ValueState.ok(
                'cu_fino_filtrado_pagable',
                '1.886',
            ),
        },
    )
