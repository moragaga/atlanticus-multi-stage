# Espejo comentado: ejemplo de lo poco que debe escribir un consumidor de ada-composition-process.
from __future__ import annotations

from datetime import UTC, date, datetime

from dash import html

from ada.compositions.process import create_process_tool_composition
from ada.contracts.tool_manifest import ToolScope
from ada.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.features.alarms.notifications import AlarmStatusState, build_alarm_status
from ada.runtime.web import RuntimeSnapshot, SourceState
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import GlobalIndicatorMeasurementState, GlobalIndicatorState
from ada.ui.shell.header import HeaderIndicatorPlacement, create_header_state
from ada.ui.shell.time_status import create_time_status_state

from .definition import (
    build_dashboard_configuration,
    build_manifest,
    build_polling_settings,
    build_renderer_registry,
)

# La herramienta concreta solo combina definición, renderers y estados de shell.
MANIFEST = build_manifest()
COMPOSITION = create_process_tool_composition(
    MANIFEST,
    dashboard_configuration=build_dashboard_configuration(),
    renderers=build_renderer_registry(),
    polling=build_polling_settings(),
)


# ProcessToolComposition entrega la aplicación visual completa desde esos contratos.
def build_process_base_tool():
    return COMPOSITION.build_tool(
        header_state=_build_header_state(),
        alarm_management_slot=_build_alarm_management(),
        alarm_status_slot=build_alarm_status(AlarmStatusState(active_count=0, managed_count=0)),
        time_status_state=create_time_status_state(
            manifest=MANIFEST,
            snapshot=_runtime_snapshot(),
        ),
        alarm_content=html.Div(
            'Sin alarmas activas',
            className='process-base__alarm-empty',
        ),
        layout_id='process-base-layout',
        class_name='process-base',
    )


def _build_header_state():
    return create_header_state(
        manifest=MANIFEST,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date.today()),
        ),
        application_name='ADA',
        global_indicators=tuple(
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scope=ToolScope.PLANT,
                indicator=indicator,
            )
            for indicator in _global_indicators()
        ),
    )


def _global_indicators() -> tuple[GlobalIndicatorState, ...]:
    return (
        _indicator('throughput', 'Throughput', 't/h', '98,2', '100'),
        _indicator('recovery', 'Recuperación', '%', '91,4', '92'),
        _indicator('quality', 'Calidad', '%', '0,61', '0,60'),
        _indicator('production', 'Producción', 't', '1.420', '1.500'),
    )


def _indicator(
    key: str,
    label: str,
    unit: str,
    real_value: str,
    plan_value: str,
) -> GlobalIndicatorState:
    return GlobalIndicatorState(
        key=key,
        label=label,
        unit=unit,
        measurements=(
            GlobalIndicatorMeasurementState.temporal(
                real_value,
                temporality='Turno',
                plan_value=plan_value,
            ),
        ),
    )


def _build_alarm_management():
    state = create_alarm_management_summary_state(
        manifest=MANIFEST,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key='alarm_management',
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=100,
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
