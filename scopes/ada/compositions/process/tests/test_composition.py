from datetime import UTC, date, datetime

import pytest
from dash import html

from ada.compositions.process import ProcessCompositionError, create_process_tool_composition
from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.features.alarms.notifications import AlarmStatusState, build_alarm_status
from ada.features.dashboard import DashboardToolConfiguration
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.components.global_indicator import GlobalIndicatorMeasurementState, GlobalIndicatorState
from ada.ui.shell.header import HeaderIndicatorPlacement, create_header_state


def _manifest():
    scope = ToolScope.PLANT
    return build_process_manifest(
        tool_key='process_composition_reference',
        display_name='Process Composition Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=scope,
        body_sections=(
            ToolSection(
                key='upstream',
                display_name='Upstream',
                kind=ToolSectionKind.COMPONENT,
                scope=scope,
                parent_key='body',
                targets=(ToolTarget.KPI,),
                layout_role=ProcessBodySection.LEFT,
            ),
            ToolSection(
                key='process',
                display_name='Process',
                kind=ToolSectionKind.COMPONENT,
                scope=scope,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                key='downstream',
                display_name='Downstream',
                kind=ToolSectionKind.COMPONENT,
                scope=scope,
                parent_key='body',
                targets=(ToolTarget.KPI,),
                layout_role=ProcessBodySection.RIGHT,
            ),
            ToolSection(
                component='upstream',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=scope,
            ),
            ToolSection(
                component='process',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=scope,
                targets=(ToolTarget.ALARM,),
            ),
            ToolSection(
                component='downstream',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=scope,
            ),
        ),
    )


def _header_state(manifest):
    indicator = GlobalIndicatorState(
        key='throughput',
        label='Throughput',
        unit='t/h',
        measurements=(
            GlobalIndicatorMeasurementState.temporal(
                '100',
                temporality='Turno',
                plan_value='110',
            ),
        ),
    )
    return create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 17)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderIndicatorPlacement(
                section_key='global_indicators',
                scope=ToolScope.PLANT,
                indicator=indicator,
            ),
        ),
    )


def _alarm_management(manifest):
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key='alarm_management',
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=100,
            ),
        ),
    )
    return build_alarm_management_summary(state)


def _props(component):
    return component.to_plotly_json()['props']


def _walk(component):
    yield component
    children = _props(component).get('children')
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = (children,)
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def test_process_composition_builds_complete_tool_boundary_with_construction_cards() -> None:
    manifest = _manifest()
    composition = create_process_tool_composition(
        manifest,
        dashboard_configuration=DashboardToolConfiguration(),
    )

    tool = composition.build_tool(
        header_state=_header_state(manifest),
        alarm_management_slot=_alarm_management(manifest),
        alarm_status_slot=build_alarm_status(AlarmStatusState(active_count=0, managed_count=0)),
        alarm_content=html.Div('Alarm queue'),
        layout_id='process-base-layout',
    )
    nodes = tuple(_walk(tool))

    assert any(_props(node).get('data-ada-process-tool') == manifest.tool_key for node in nodes)
    assert any(
        _props(node).get('data-ada-operational-shell') == manifest.tool_key for node in nodes
    )
    assert any(_props(node).get('data-section-key') == 'alarm_status' for node in nodes)
    assert any(_props(node).get('data-ada-process-alarm-surface') == 'true' for node in nodes)
    assert any(_props(node).get('data-ada-alarm-baseline') == 'process' for node in nodes)
    assert any(_props(node).get('data-ada-slot-key') == 'center' for node in nodes)
    cards = [node for node in nodes if _props(node).get('data-ada-component-card') == 'true']
    assert len(cards) == 3
    assert all('ada-process-tool__card' in _props(card)['className'] for card in cards)


def test_process_composition_mount_uses_dashboard_content_boundaries() -> None:
    composition = create_process_tool_composition(_manifest())

    slot = composition.mount.slot('process', 'main')

    assert _props(slot.content)['className'] == 'ada-dashboard-content-slot'
    assert _props(slot.overlay)['children'] is not None


def test_process_composition_rejects_integrated_operations_manifest() -> None:
    with pytest.raises(ProcessCompositionError, match='only layout components'):
        create_process_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)


def test_process_composition_is_runnable_with_default_construction_shell_slots() -> None:
    manifest = _manifest()
    composition = create_process_tool_composition(manifest)

    tool = composition.build_tool(header_state=_header_state(manifest))
    nodes = tuple(_walk(tool))
    readiness = {
        _props(node).get('data-ready-name'): _props(node).get('data-cover')
        for node in nodes
        if _props(node).get('data-ready-name')
    }

    assert readiness['global-indicators'] == 'none'
    assert readiness['alarm-management'] == 'construction'
    assert readiness['alarm-status'] == 'construction'
    assert readiness['time-status'] == 'construction'


def _projection(manifest):
    return ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='r5.2-test',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=manifest,
    )


def test_process_composition_mounts_projection_wrappers_and_r3_stores() -> None:
    manifest = _manifest()
    projection = _projection(manifest)
    composition = create_process_tool_composition(
        manifest,
        projection=projection,
    )

    tool = composition.build_tool(header_state=_header_state(manifest))
    nodes = tuple(_walk(tool))
    ids = {_props(node).get('id') for node in nodes if _props(node).get('id') is not None}

    assert projection.runtime.component('global_indicators').wrapper_id in ids
    assert projection.runtime.component('time_status').wrapper_id in ids
    assert projection.runtime.component('process').wrapper_id in ids
    assert (
        projection.runtime.subcomponent(
            component_key='process',
            subcomponent_key='main',
        ).wrapper_id
        in ids
    )
    assert projection.runtime.component('process').kpi_latest_store_id in ids
    assert projection.runtime.component('process').kpi_timeseries_store_id in ids


def test_process_rejects_projection_for_another_tool() -> None:
    manifest = _manifest()
    other = build_process_manifest(
        tool_key='other_process',
        display_name='Other Process',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='process',
                display_name='Process',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                component='process',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
        ),
    )

    with pytest.raises(ProcessCompositionError, match='projection tool key'):
        create_process_tool_composition(
            manifest,
            projection=_projection(other),
        )
