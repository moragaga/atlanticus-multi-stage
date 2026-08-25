from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ada.applications.reference.runtime import ADA_RUNTIME_SERVICE
from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.runtime.web import AdaRuntime, GuardState, resolve_guard
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.framework.core import coerce_display_value
from ada.ui.shell.header import HeaderIndicatorPlacement, HeaderSectionStates, create_header_state
from atlanticus.web.services import ServiceRegistry


@dataclass(frozen=True, slots=True)
class _ReferenceIndicatorDefinition:
    key: str
    label: str
    unit: str
    scope: ToolScope
    plan: str
    measurements: tuple[tuple[str, str], ...]
    include_last_measurement: bool = False


_INDICATOR_DEFINITIONS = (
    _ReferenceIndicatorDefinition(
        key='transportado',
        label='Transportado',
        unit='kt',
        scope=ToolScope.MINE,
        plan='220',
        measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
        include_last_measurement=True,
    ),
    _ReferenceIndicatorDefinition(
        key='molienda',
        label='Molienda',
        unit='kt',
        scope=ToolScope.PLANT,
        plan='210',
        measurements=(('dia', 'Día'), ('semana', 'Semana')),
    ),
    _ReferenceIndicatorDefinition(
        key='ley_cobre',
        label='Ley de Cobre',
        unit='%',
        scope=ToolScope.PLANT,
        plan='0,55',
        measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
    ),
    _ReferenceIndicatorDefinition(
        key='recuperacion_cu',
        label='Recuperación Cu',
        unit='%',
        scope=ToolScope.PLANT,
        plan='90,5',
        measurements=(('dia', 'Día'), ('semana', 'Semana')),
        include_last_measurement=True,
    ),
    _ReferenceIndicatorDefinition(
        key='cu_fino_producido',
        label='Cu Fino Producido',
        unit='t',
        scope=ToolScope.PLANT,
        plan='1.050',
        measurements=(('turno', 'Turno'), ('dia', 'Día'), ('mes', 'Mes')),
        include_last_measurement=True,
    ),
    _ReferenceIndicatorDefinition(
        key='mo_fino_producido',
        label='Mo Fino Producido',
        unit='t',
        scope=ToolScope.PLANT,
        plan='33',
        measurements=(('dia', 'Día'), ('semana', 'Semana')),
    ),
    _ReferenceIndicatorDefinition(
        key='expit',
        label='ExPit',
        unit='t',
        scope=ToolScope.MINE,
        plan='426',
        measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
    ),
    _ReferenceIndicatorDefinition(
        key='cu_fino_filtrado_pagable',
        label='Cu Fino Filtr. Pag.',
        unit='t',
        scope=ToolScope.PLANT,
        plan='1.784',
        measurements=(('dia', 'Día'), ('mes', 'Mes')),
        include_last_measurement=True,
    ),
)


def build_reference_header_state(services: ServiceRegistry, manifest: ToolManifest):
    runtime = services.require(ADA_RUNTIME_SERVICE, AdaRuntime)
    snapshot = runtime.current().snapshot
    indicators_guard = resolve_guard(snapshot, required_sources=('pi',))
    return build_reference_header_state_from_values(
        manifest,
        values={
            definition.key: snapshot.value(definition.key) for definition in _INDICATOR_DEFINITIONS
        },
        cover=_cover_from_guard(indicators_guard.state),
    )


def build_reference_header_state_from_values(
    manifest: ToolManifest,
    *,
    values: Mapping[str, object],
    cover: ComponentCover | None = None,
):
    return create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=tuple(
            _indicator(
                manifest,
                definition=definition,
                value=values.get(definition.key),
            )
            for definition in _INDICATOR_DEFINITIONS
        ),
        section_states=HeaderSectionStates(
            global_indicators=cover or ComponentCover.none(),
        ),
    )


def _cover_from_guard(state: GuardState) -> ComponentCover:
    return {
        GuardState.READY: ComponentCover.none,
        GuardState.CONSTRUCTION: ComponentCover.construction,
        GuardState.STALE: ComponentCover.stale,
        GuardState.SOURCE_ERROR: ComponentCover.source_error,
        GuardState.COMPONENT_ERROR: ComponentCover.component_error,
    }[state]()


def _indicator(
    manifest: ToolManifest,
    *,
    definition: _ReferenceIndicatorDefinition,
    value: object,
) -> HeaderIndicatorPlacement:
    section_key = manifest.subcomponent(
        component='global_indicators',
        subcomponent=definition.scope.value,
    ).key
    display_value = coerce_display_value(value)
    return HeaderIndicatorPlacement(
        section_key=section_key,
        scopes=frozenset({definition.scope}),
        indicator=GlobalIndicatorState(
            key=definition.key,
            label=definition.label,
            unit=definition.unit,
            definition_key=definition.key,
            measurements=tuple(
                GlobalIndicatorMeasurementState(
                    key=measurement_key,
                    label=measurement_label,
                    actual_value=display_value,
                    plan_value=definition.plan,
                )
                for measurement_key, measurement_label in definition.measurements
            ),
            last_measurement=(
                GlobalIndicatorLastMeasurementState(actual_value=display_value)
                if definition.include_last_measurement
                else None
            ),
        ),
    )
