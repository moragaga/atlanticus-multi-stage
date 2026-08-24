from __future__ import annotations

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
from ada.ui.components.global_indicator import GlobalIndicatorMeasurementState, GlobalIndicatorState
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
                section_key=_scoped_section_key(manifest, 'global_indicators', scope),
                scope=scope,
                indicator=indicator,
            )
            for scope, indicator in _global_indicators()
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


def _global_indicators() -> tuple[tuple[ToolScope, GlobalIndicatorState], ...]:
    return (
        (ToolScope.MINE, _indicator('transported', 'Transportado', 'kt', '220', '220')),
        (ToolScope.MINE, _indicator('expit', 'ExPit', 'kt', '426', '426')),
        (ToolScope.PLANT, _indicator('grinding', 'Molienda', 'kt', '210', '210')),
        (ToolScope.PLANT, _indicator('copper_grade', 'Ley de Cobre', '%', '0,55', '0,55')),
        (ToolScope.PLANT, _indicator('copper_recovery', 'Recuperación Cu', '%', '90,5', '90,5')),
        (ToolScope.PLANT, _indicator('fine_copper', 'Cu Fino Producido', 't', '1.050', '1.050')),
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
                temporality='Día',
                plan_value=plan_value,
            ),
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
