from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from ada.applications.reference.runtime import ADA_RUNTIME_SERVICE
from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.runtime.web import AdaRuntime, GuardState, resolve_guard
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.framework.core import coerce_display_value
from ada.ui.shell.header import HeaderIndicatorPlacement, HeaderSectionStates, create_header_state
from atlanticus.web.services import ServiceRegistry

_INDICATOR_DEFINITIONS = (
    ('transportado', 'Transportado', 'kt', ToolScope.MINE, '220'),
    ('molienda', 'Molienda', 'kt', ToolScope.PLANT, '210'),
    ('ley_cobre', 'Ley de Cobre', '%', ToolScope.PLANT, '0,55'),
    ('recuperacion_cu', 'Recuperación Cu', '%', ToolScope.PLANT, '90,5'),
    ('cu_fino_producido', 'Cu Fino Producido', 't', ToolScope.PLANT, '1.050'),
    ('mo_fino_producido', 'Mo Fino Producido', 't', ToolScope.PLANT, '33'),
    ('expit', 'ExPit', 't', ToolScope.MINE, '426'),
    (
        'cu_fino_filtrado_pagable',
        'Cu Fino Filtr. Pag.',
        't',
        ToolScope.PLANT,
        '1.784',
    ),
)


def build_reference_header_state(services: ServiceRegistry, manifest: ToolManifest):
    runtime = services.require(ADA_RUNTIME_SERVICE, AdaRuntime)
    snapshot = runtime.current().snapshot
    indicators_guard = resolve_guard(snapshot, required_sources=('pi',))
    return build_reference_header_state_from_values(
        manifest,
        values={key: snapshot.value(key) for key, *_ in _INDICATOR_DEFINITIONS},
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
                key=key,
                label=label,
                unit=unit,
                scope=scope,
                plan=plan,
                value=values.get(key),
            )
            for key, label, unit, scope, plan in _INDICATOR_DEFINITIONS
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
    key: str,
    label: str,
    unit: str,
    scope: ToolScope,
    plan: str,
    value: object,
) -> HeaderIndicatorPlacement:
    subcomponent = {
        ToolScope.MINE: 'mine',
        ToolScope.PLANT: 'plant',
    }[scope]
    section_key = manifest.subcomponent(
        component='global_indicators',
        subcomponent=subcomponent,
    ).key
    display_value = coerce_display_value(value)
    return HeaderIndicatorPlacement(
        section_key=section_key,
        scope=scope,
        indicator=GlobalIndicatorState(
            key=key,
            label=label,
            unit=unit,
            definition_key=key,
            measurements=(
                GlobalIndicatorMeasurementState.temporal(
                    display_value,
                    temporality='Día',
                    plan_value=plan,
                ),
                GlobalIndicatorMeasurementState.temporal(
                    display_value,
                    temporality='Semana',
                    plan_value=plan,
                ),
            ),
        ),
    )
