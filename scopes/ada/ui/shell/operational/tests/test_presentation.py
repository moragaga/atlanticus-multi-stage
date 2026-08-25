from datetime import date

import pytest
from dash import html
from dash.development.base_component import Component

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.ui.components.branding import ATLANTICUS_BRAND_MANIFEST, BrandContext, resolve_brand
from ada.ui.shell.header import create_header_state
from ada.ui.shell.operational import OperationalShellError, build_ada_operational_shell


def _manifest(tool_key: str = 'generic_process'):
    return build_process_manifest(
        tool_key=tool_key,
        display_name='Generic Process',
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


def _header_state(manifest):
    return create_header_state(
        manifest=manifest,
        brand=resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 25)),
        ),
        application_name='ADA',
        global_indicators=(),
    )


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
        if isinstance(child, Component):
            yield from _walk(child)


def test_operational_shell_lifts_without_runtime_data_or_body_content() -> None:
    manifest = _manifest()

    shell = build_ada_operational_shell(
        manifest,
        header_state=_header_state(manifest),
    )
    nodes = tuple(_walk(shell))
    root = next(node for node in nodes if _props(node).get('data-ada-operational-shell'))
    readiness = {
        _props(node).get('data-ready-name'): _props(node).get('data-cover')
        for node in nodes
        if _props(node).get('data-ready-name')
    }

    assert _props(root)['data-ada-operational-shell'] == manifest.tool_key
    assert 'ada-operational-shell' in _props(root)['className']
    assert readiness['global-indicators'] == 'none'
    assert readiness['alarm-management'] == 'construction'
    assert readiness['alarm-status'] == 'construction'
    assert readiness['time-status'] == 'construction'
    assert any(
        'ada-operational-shell__alarm-surface' in (_props(node).get('className') or '')
        for node in nodes
    )
    assert any(
        'ada-operational-shell__body' in (_props(node).get('className') or '') for node in nodes
    )


def test_operational_shell_preserves_injected_alarm_body_and_runtime_hosts() -> None:
    manifest = _manifest()

    shell = build_ada_operational_shell(
        manifest,
        header_state=_header_state(manifest),
        alarm_children=(html.Div('alarm', id='alarm-content'),),
        body_content=html.Div('body', id='body-content'),
        runtime_hosts=(html.Div(id='runtime-host', style={'display': 'none'}),),
        shell_class_name='tool-shell',
        time_status_class_name='tool-time',
        alarm_surface_class_name='tool-alarms',
        body_class_name='tool-body',
        shell_attributes={'data-tool-kind': 'process'},
        alarm_surface_attributes={'data-alarm-mode': 'generic'},
    )
    nodes = tuple(_walk(shell))
    by_id = {_props(node).get('id'): node for node in nodes if _props(node).get('id') is not None}
    root = next(node for node in nodes if _props(node).get('data-ada-operational-shell'))
    alarm_surface = next(
        node
        for node in nodes
        if 'ada-operational-shell__alarm-surface' in (_props(node).get('className') or '')
    )

    assert 'tool-shell' in _props(root)['className']
    assert _props(root)['data-tool-kind'] == 'process'
    assert _props(alarm_surface)['data-alarm-mode'] == 'generic'
    assert {'alarm-content', 'body-content', 'runtime-host'} <= by_id.keys()


def test_operational_shell_rejects_mismatched_header_identity() -> None:
    manifest = _manifest('tool_a')
    other = _manifest('tool_b')

    with pytest.raises(OperationalShellError, match='Header state tool key'):
        build_ada_operational_shell(
            manifest,
            header_state=_header_state(other),
        )


def test_operational_shell_rejects_reserved_structure_attributes() -> None:
    manifest = _manifest()

    with pytest.raises(OperationalShellError, match='Reserved shell attributes'):
        build_ada_operational_shell(
            manifest,
            header_state=_header_state(manifest),
            shell_attributes={'className': 'override'},
        )


def test_operational_shell_applies_runtime_wrapper_to_time_status() -> None:
    manifest = _manifest()

    shell = build_ada_operational_shell(
        manifest,
        header_state=_header_state(manifest),
        runtime_component_wrapper_ids={
            'time_status': 'ada-runtime-component-time_status',
        },
    )
    node = next(
        item
        for item in _walk(shell)
        if _props(item).get('id') == 'ada-runtime-component-time_status'
    )

    assert 'ada-operational-shell__time-status' in _props(node)['className']
