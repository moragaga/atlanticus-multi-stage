from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
        revision='reference-1',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy(
                'pi',
                updated_at_utc=now - timedelta(minutes=8),
                stale=True,
            ),
            'dispatch': SourceState.healthy(
                'dispatch',
                updated_at_utc=now - timedelta(seconds=20),
            ),
        },
        values={key: ValueState.invalid(key) for key in REFERENCE_INDICATOR_KEYS},
    )
