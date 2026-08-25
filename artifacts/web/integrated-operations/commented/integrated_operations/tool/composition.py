from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from ada.compositions.integrated_operations import (
    IntegratedOperationsToolComposition,
    create_integrated_operations_tool_composition,
)
from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.features.alarms.notifications import AlarmStatusState, build_alarm_status
from ada.runtime.web import RuntimeSnapshot, SourceState
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import (
    GlobalIndicatorLastMeasurementState,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
)
from ada.ui.shell.header import HeaderIndicatorPlacement, create_header_state
from ada.ui.shell.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
)
from ada.ui.shell.time_status import create_time_status_state
from integrated_operations.tool.configuration import (
    build_dashboard_configuration,
    build_polling_settings,
    build_renderer_registry,
)


# Define el catálogo visual temporal que alimenta el Header real mientras se integra el runtime.
@dataclass(frozen=True, slots=True)
class _IndicatorDefinition:
    key: str
    label: str
    unit: str
    scope: ToolScope
    actual_value: str
    plan_value: str
    measurements: tuple[tuple[str, str], ...]
    last_value: str | None = None


def build_integrated_operations_composition(
    manifest: ToolManifest,
) -> IntegratedOperationsToolComposition:
    return create_integrated_operations_tool_composition(
        manifest,
        dashboard_configuration=build_dashboard_configuration(manifest),
        renderers=build_renderer_registry(manifest),
        polling=build_polling_settings(),
    )


def build_integrated_operations_tool(composition: IntegratedOperationsToolComposition):
    manifest = composition.manifest
    return composition.build_tool(
        header_state=_build_header_state(manifest),
        alarm_management_slot=_build_alarm_management(manifest),
        alarm_status_slot=build_alarm_status(AlarmStatusState(active_count=0, managed_count=0)),
        time_status_state=create_time_status_state(
            manifest=manifest,
            snapshot=_runtime_snapshot(),
        ),
        desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
        mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
        layout_id='integrated-operations-layout',
        class_name='integrated-operations',
    )


def _build_header_state(manifest: ToolManifest):
    return create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=tuple(
            HeaderIndicatorPlacement(
                section_key=_scoped_section_key(
                    manifest,
                    'global_indicators',
                    definition.scope,
                ),
                scopes=frozenset({definition.scope}),
                indicator=_indicator(definition),
            )
            for definition in _global_indicator_definitions()
        ),
    )


def _scoped_section_key(
    manifest: ToolManifest,
    component: str,
    scope: ToolScope,
) -> str:
    return manifest.subcomponent(
        component=component,
        subcomponent=scope.value,
    ).key


# Mantiene tres slots visuales totales: tres mediciones normales o dos normales más latest.
def _global_indicator_definitions() -> tuple[_IndicatorDefinition, ...]:
    return (
        _IndicatorDefinition(
            key='transported',
            label='Transportado',
            unit='kt',
            scope=ToolScope.MINE,
            actual_value='198',
            plan_value='220',
            measurements=(('turno', 'Turno'), ('dia', 'Día')),
            last_value='198',
        ),
        _IndicatorDefinition(
            key='grinding',
            label='Molienda',
            unit='kt',
            scope=ToolScope.PLANT,
            actual_value='205',
            plan_value='210',
            measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
        ),
        _IndicatorDefinition(
            key='copper_grade',
            label='Ley de Cobre',
            unit='%',
            scope=ToolScope.PLANT,
            actual_value='0,53',
            plan_value='0,55',
            measurements=(('turno', 'Turno'), ('dia', 'Día')),
            last_value='0,53',
        ),
        _IndicatorDefinition(
            key='copper_recovery',
            label='Recuperación Cu',
            unit='%',
            scope=ToolScope.PLANT,
            actual_value='89,8',
            plan_value='90,5',
            measurements=(('turno', 'Turno'), ('dia', 'Día')),
            last_value='89,8',
        ),
        _IndicatorDefinition(
            key='fine_copper',
            label='Cu Fino Producido',
            unit='t',
            scope=ToolScope.PLANT,
            actual_value='1.012',
            plan_value='1.050',
            measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
        ),
        _IndicatorDefinition(
            key='fine_moly',
            label='Mo Fino Producido',
            unit='t',
            scope=ToolScope.PLANT,
            actual_value='28',
            plan_value='33',
            measurements=(('turno', 'Turno'), ('dia', 'Día'), ('semana', 'Semana')),
        ),
        _IndicatorDefinition(
            key='expit',
            label='ExPit',
            unit='t',
            scope=ToolScope.MINE,
            actual_value='376',
            plan_value='426',
            measurements=(('turno', 'Turno'), ('dia', 'Día')),
            last_value='376',
        ),
        _IndicatorDefinition(
            key='filtered_copper_paid',
            label='Cu Fino Filtr. Pag.',
            unit='t',
            scope=ToolScope.PLANT,
            actual_value='1.886',
            plan_value='1.784',
            measurements=(('turno', 'Turno'), ('dia', 'Día')),
            last_value='1.886',
        ),
    )


# Convierte la definición declarativa en el estado reusable del componente Global Indicator.
def _indicator(definition: _IndicatorDefinition) -> GlobalIndicatorState:
    return GlobalIndicatorState(
        key=definition.key,
        label=definition.label,
        unit=definition.unit,
        measurements=tuple(
            GlobalIndicatorMeasurementState(
                key=measurement_key,
                label=measurement_label,
                actual_value=definition.actual_value,
                plan_value=definition.plan_value,
            )
            for measurement_key, measurement_label in definition.measurements
        ),
        last_measurement=(
            GlobalIndicatorLastMeasurementState(actual_value=definition.last_value)
            if definition.last_value is not None
            else None
        ),
    )


def _build_alarm_management(manifest: ToolManifest):
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key=_scoped_section_key(manifest, 'alarm_management', ToolScope.MINE),
                scope=ToolScope.MINE,
                group='G3',
                management_percentage=60,
                tone=AlarmManagementSummaryTone.NEUTRAL,
            ),
            AlarmManagementSummarySegmentState(
                section_key=_scoped_section_key(manifest, 'alarm_management', ToolScope.PLANT),
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=45,
                tone=AlarmManagementSummaryTone.NEUTRAL,
            ),
        ),
    )
    return build_alarm_management_summary(state)


def _runtime_snapshot() -> RuntimeSnapshot:
    now = datetime.now(UTC)
    return RuntimeSnapshot(
        revision=now.strftime('%Y%m%d%H%M%S%f'),
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
        values={},
    )
