from datetime import date

from ada.applications.reference.runtime import ADA_RUNTIME_SERVICE
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolScope
from ada.runtime.web import AdaRuntime, GuardState, resolve_guard
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.framework.core import coerce_display_value
from ada.ui.shell.header import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    HeaderIndicatorPlacement,
    HeaderSectionStates,
    HeaderTone,
    create_header_state,
)
from atlanticus.web.services import ServiceRegistry


# La referencia combina estados sanos, degradados, stale y construction desde el primer render.
def build_reference_header_state(services: ServiceRegistry):
    runtime = services.require(ADA_RUNTIME_SERVICE, AdaRuntime)
    snapshot = runtime.current().snapshot
    indicators_guard = resolve_guard(snapshot, required_sources=('pi',))
    return create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=(
            _indicator(snapshot, 'transportado', 'Transportado', 'kt', ToolScope.MINE, '220'),
            _indicator(snapshot, 'molienda', 'Molienda', 'kt', ToolScope.PLANT, '210'),
            _indicator(snapshot, 'ley_cobre', 'Ley de Cobre', '%', ToolScope.PLANT, '0,55'),
            _indicator(
                snapshot,
                'recuperacion_cu',
                'Recuperación Cu',
                '%',
                ToolScope.PLANT,
                '90,5',
            ),
            _indicator(
                snapshot,
                'cu_fino_producido',
                'Cu Fino Producido',
                't',
                ToolScope.PLANT,
                '1.050',
            ),
            _indicator(
                snapshot,
                'mo_fino_producido',
                'Mo Fino Producido',
                't',
                ToolScope.PLANT,
                '33',
            ),
            _indicator(snapshot, 'expit', 'ExPit', 't', ToolScope.MINE, '426'),
            _indicator(
                snapshot,
                'cu_fino_filtrado_pagable',
                'Cu Fino Filtr. Pag.',
                't',
                ToolScope.PLANT,
                '1.784',
            ),
        ),
        alarm_management=AlarmManagementState(
            segments=(
                AlarmManagementSegmentState(
                    section_key='alarm_management_mine',
                    scope=ToolScope.MINE,
                    group='G3',
                    management_percentage=60,
                    tone=HeaderTone.ATTENTION,
                ),
                AlarmManagementSegmentState(
                    section_key='alarm_management_plant',
                    scope=ToolScope.PLANT,
                    group='G1',
                    management_percentage=45,
                    tone=HeaderTone.CRITICAL,
                ),
            )
        ),
        section_states=HeaderSectionStates(
            global_indicators=_cover_from_guard(indicators_guard.state),
            alarm_management=ComponentCover.stale(),
            alarm_status=ComponentCover.construction(),
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
    snapshot,
    key: str,
    label: str,
    unit: str,
    scope: ToolScope,
    plan: str,
) -> HeaderIndicatorPlacement:
    section_key = {
        ToolScope.MINE: 'global_indicators_mine',
        ToolScope.PLANT: 'global_indicators_plant',
    }[scope]
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
