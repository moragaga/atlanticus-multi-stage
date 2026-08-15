# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
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


def build_reference_header_state(services: ServiceRegistry, manifest: ToolManifest):
    runtime = services.require(ADA_RUNTIME_SERVICE, AdaRuntime)
    snapshot = runtime.current().snapshot
    indicators_guard = resolve_guard(snapshot, required_sources=('pi',))
    return create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=(
            _indicator(manifest, snapshot, 'transportado', 'Transportado', 'kt', ToolScope.MINE, '220'),
            _indicator(manifest, snapshot, 'molienda', 'Molienda', 'kt', ToolScope.PLANT, '210'),
            _indicator(manifest, snapshot, 'ley_cobre', 'Ley de Cobre', '%', ToolScope.PLANT, '0,55'),
            _indicator(
                manifest,
                snapshot,
                'recuperacion_cu',
                'Recuperación Cu',
                '%',
                ToolScope.PLANT,
                '90,5',
            ),
            _indicator(
                manifest,
                snapshot,
                'cu_fino_producido',
                'Cu Fino Producido',
                't',
                ToolScope.PLANT,
                '1.050',
            ),
            _indicator(
                manifest,
                snapshot,
                'mo_fino_producido',
                'Mo Fino Producido',
                't',
                ToolScope.PLANT,
                '33',
            ),
            _indicator(manifest, snapshot, 'expit', 'ExPit', 't', ToolScope.MINE, '426'),
            _indicator(
                manifest,
                snapshot,
                'cu_fino_filtrado_pagable',
                'Cu Fino Filtr. Pag.',
                't',
                ToolScope.PLANT,
                '1.784',
            ),
        ),
        section_states=HeaderSectionStates(
            global_indicators=_cover_from_guard(indicators_guard.state),
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
    snapshot,
    key: str,
    label: str,
    unit: str,
    scope: ToolScope,
    plan: str,
) -> HeaderIndicatorPlacement:
    # El consumidor declara identidades semánticas; el manifest resuelve la key técnica derivada.
    subcomponent = {
        ToolScope.MINE: 'mine',
        ToolScope.PLANT: 'plant',
    }[scope]
    section_key = manifest.subcomponent(
        component='global_indicators',
        subcomponent=subcomponent,
    ).key
    value = coerce_display_value(snapshot.value(key))
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
                    value,
                    temporality='Día',
                    plan_value=plan,
                ),
                GlobalIndicatorMeasurementState.temporal(
                    value,
                    temporality='Semana',
                    plan_value=plan,
                ),
            ),
        ),
    )
