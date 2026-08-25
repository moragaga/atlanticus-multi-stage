from datetime import UTC, date, datetime

import pytest

from ada.compositions.integrated_operations import (
    IntegratedOperationsCompositionError,
    create_integrated_operations_tool_composition,
)
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


def _scoped_section_key(component: str, scope: ToolScope) -> str:
    return INTEGRATED_OPERATIONS_MANIFEST.subcomponent(
        component=component,
        subcomponent=scope.value,
    ).key


def _header_state():
    indicator = GlobalIndicatorState(
        key='throughput',
        label='Throughput',
        unit='t/h',
        measurements=(
            GlobalIndicatorMeasurementState.temporal('100', temporality='Turno', plan_value='110'),
        ),
    )
    return create_header_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 17)),
        ),
        application_name='ADA',
        global_indicators=(
            HeaderIndicatorPlacement(
                section_key=_scoped_section_key('global_indicators', ToolScope.MINE),
                scope=ToolScope.MINE,
                indicator=indicator,
            ),
        ),
    )


def _management():
    return build_alarm_management_summary(
        create_alarm_management_summary_state(
            manifest=INTEGRATED_OPERATIONS_MANIFEST,
            segments=(
                AlarmManagementSummarySegmentState(
                    section_key=_scoped_section_key('alarm_management', ToolScope.MINE),
                    scope=ToolScope.MINE,
                    group='G1',
                    management_percentage=100,
                ),
                AlarmManagementSummarySegmentState(
                    section_key=_scoped_section_key('alarm_management', ToolScope.PLANT),
                    scope=ToolScope.PLANT,
                    group='G2',
                    management_percentage=100,
                ),
            ),
        )
    )


def test_integrated_operations_composition_builds_full_tool_boundary() -> None:
    composition = create_integrated_operations_tool_composition(
        INTEGRATED_OPERATIONS_MANIFEST,
        dashboard_configuration=DashboardToolConfiguration(),
    )
    tool = composition.build_tool(
        header_state=_header_state(),
        alarm_management_slot=_management(),
        alarm_status_slot=build_alarm_status(AlarmStatusState(active_count=0, managed_count=0)),
        layout_id='io-base-layout',
    )
    nodes = tuple(_walk(tool))

    assert any(
        _props(node).get('data-ada-integrated-operations-tool') == 'integrated_operations'
        for node in nodes
    )
    assert any(
        _props(node).get('data-ada-operational-shell') == 'integrated_operations' for node in nodes
    )
    assert any(_props(node).get('data-section-key') == 'alarm_status' for node in nodes)
    assert any(
        _props(node).get('data-ada-integrated-operations-alarm-surface') == 'true' for node in nodes
    )
    assert any(
        _props(node).get('data-ada-alarm-baseline') == 'integrated-operations' for node in nodes
    )
    assert any(_props(node).get('data-ada-io-scope-key') == 'mine' for node in nodes)
    assert any(_props(node).get('data-ada-io-scope-key') == 'plant' for node in nodes)
    assert any(_props(node).get('id') == 'io-base-layout' for node in nodes)


def test_integrated_operations_baseline_declares_real_scope_mapping() -> None:
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    tool = composition.build_tool(header_state=_header_state())
    baseline = next(
        node
        for node in _walk(tool)
        if _props(node).get('data-ada-alarm-baseline') == 'integrated-operations'
    )
    nodes = [
        node
        for node in _walk(baseline)
        if _props(node).get('data-ada-alarm-target-kind') == 'component'
    ]

    assert [_props(node)['data-ada-alarm-scope'] for node in nodes[:4]] == ['mine'] * 4
    assert [_props(node)['data-ada-alarm-scope'] for node in nodes[4:]] == ['plant'] * 5


def test_shared_carguio_transporte_card_starts_in_construction() -> None:
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    tool = composition.build_tool(header_state=_header_state())
    shared = next(
        node
        for node in _walk(tool)
        if _props(node).get('data-ada-subcomponent-key') == 'carguio_gestion_carguio_turno'
    )

    assert any(_props(node).get('data-overlay-kind') == 'construction' for node in _walk(shared))


def test_integrated_operations_composition_exposes_presentation_controls_without_removing_scopes() -> (
    None
):
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    tool = composition.build_tool(header_state=_header_state())
    nodes = tuple(_walk(tool))

    targets = {
        _props(node).get('data-ada-io-presentation-target')
        for node in nodes
        if _props(node).get('data-ada-io-presentation-target')
    }
    scopes = {
        _props(node).get('data-ada-io-scope-key')
        for node in nodes
        if _props(node).get('data-ada-io-scope-key')
    }

    assert targets == {'overview', 'mine', 'plant'}
    assert scopes == {'mine', 'plant'}


def test_integrated_operations_alarm_surface_reserves_empty_content_boundary() -> None:
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    tool = composition.build_tool(header_state=_header_state())
    nodes = tuple(_walk(tool))
    content = next(
        node
        for node in nodes
        if _props(node).get('className') == 'ada-integrated-operations-tool__alarm-content'
    )

    assert _props(content)['children'] == []


def test_integrated_operations_exposes_overview_indicator_count_for_stable_zoom_cells() -> None:
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    tool = composition.build_tool(header_state=_header_state())
    root = next(
        node
        for node in _walk(tool)
        if _props(node).get('data-ada-integrated-operations-tool') == 'integrated_operations'
    )

    assert _props(root)['style']['--ada-io-overview-indicator-count'] == '1'


def _projection(manifest=INTEGRATED_OPERATIONS_MANIFEST):
    return ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='r5.2-test',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=manifest,
    )


def test_integrated_operations_mounts_projection_wrappers_and_r3_stores() -> None:
    projection = _projection()
    composition = create_integrated_operations_tool_composition(
        INTEGRATED_OPERATIONS_MANIFEST,
        projection=projection,
    )

    tool = composition.build_tool(header_state=_header_state())
    nodes = tuple(_walk(tool))
    ids = [_props(node).get('id') for node in nodes if _props(node).get('id') is not None]
    shared_wrapper_id = projection.runtime.subcomponent(
        component_key='carguio',
        subcomponent_key='gestion_carguio_turno',
    ).wrapper_id

    assert projection.runtime.component('global_indicators').wrapper_id in ids
    assert projection.runtime.component('time_status').wrapper_id in ids
    assert projection.runtime.component('molienda').wrapper_id in ids
    assert projection.runtime.component('molienda').kpi_latest_store_id in ids
    assert projection.runtime.component('molienda').kpi_timeseries_store_id in ids
    assert ids.count(shared_wrapper_id) == 1


def test_integrated_operations_rejects_projection_for_another_tool() -> None:
    scope = ToolScope.PLANT
    other = build_process_manifest(
        tool_key='other_process',
        display_name='Other Process',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=scope,
        body_sections=(
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
                component='process',
                subcomponent='main',
                display_name='Main',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=scope,
                targets=(ToolTarget.ALARM,),
            ),
        ),
    )

    with pytest.raises(IntegratedOperationsCompositionError, match='projection tool key'):
        create_integrated_operations_tool_composition(
            INTEGRATED_OPERATIONS_MANIFEST,
            projection=_projection(other),
        )
