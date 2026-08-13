from __future__ import annotations

from datetime import UTC, datetime
from functools import partial

from ada.contracts.tool_manifest import ToolManifest
from ada.runtime.web import (
    AdaRuntime,
    RuntimeDefinition,
    RuntimeSnapshot,
    RuntimeSourceDefinition,
    SourceState,
    ValueState,
)
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


def create_reference_runtime_module(manifest: ToolManifest) -> WebModule:
    return WebModule(
        name='ada-runtime',
        register_services=partial(_register_runtime, manifest=manifest),
    )


def build_reference_runtime_definition(manifest: ToolManifest) -> RuntimeDefinition:
    return RuntimeDefinition(
        sources=tuple(
            RuntimeSourceDefinition(
                key=source.key.value,
                stale_after_seconds=source.stale_after_seconds,
            )
            for source in manifest.sources
        ),
        value_keys=REFERENCE_INDICATOR_KEYS,
    )


def _register_runtime(services: ServiceRegistry, *, manifest: ToolManifest) -> None:
    runtime = _build_runtime(manifest)
    runtime.warmup()
    services.add(ADA_RUNTIME_SERVICE, runtime)


def _build_runtime(manifest: ToolManifest) -> AdaRuntime:
    return AdaRuntime(
        shape=build_reference_runtime_definition(manifest),
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
