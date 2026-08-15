import pytest
from dash import html

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
from ada.ui.layouts.process import ProcessLayoutError, build_process_layout

_PI = ToolSource(ToolSourceKey.PI, stale_after_seconds=300)
_KPI = frozenset({ToolTarget.KPI})
_ALARM = frozenset({ToolTarget.ALARM})
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_FUNCTIONAL_KEYS = {
    ProcessBodySection.LEFT: 'aguas_arriba',
    ProcessBodySection.CENTER: 'proceso_principal',
    ProcessBodySection.RIGHT: 'aguas_abajo',
    ProcessBodySection.BOTTOM: 'indicadores_inferiores',
}


def _component(role: ProcessBodySection) -> ToolSection:
    key = _FUNCTIONAL_KEYS[role]
    return ToolSection(
        key=key,
        display_name=key.replace('_', ' ').title(),
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def _card(role: ProcessBodySection) -> ToolSection:
    component = _FUNCTIONAL_KEYS[role]
    return ToolSection(
        component=component,
        subcomponent='principal',
        display_name='Principal',
        kind=ToolSectionKind.SUBCOMPONENT,
        scope=ToolScope.PLANT,
        targets=_ALARM if role is ProcessBodySection.CENTER else (),
    )


def _manifest(*roles: ProcessBodySection):
    components = tuple(_component(role) for role in roles)
    cards = tuple(_card(role) for role in roles)
    return build_process_manifest(
        tool_key='process_reference',
        display_name='Process Reference',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(*components, *cards),
    )


def _content(*roles: ProcessBodySection):
    return {_FUNCTIONAL_KEYS[role]: html.Div(role.value) for role in roles}


def _props(component):
    return component.to_plotly_json()['props']


def _columns(layout):
    main = _props(layout)['children'][0]
    return [
        (_props(slot)['data-ada-process-layout-role'], _props(slot)['className'])
        for slot in _props(main)['children']
    ]


@pytest.mark.parametrize(
    ('roles', 'expected'),
    (
        (
            (ProcessBodySection.LEFT, ProcessBodySection.CENTER, ProcessBodySection.RIGHT),
            [('left', 'col-2'), ('center', 'col-8'), ('right', 'col-2')],
        ),
        (
            (ProcessBodySection.LEFT, ProcessBodySection.CENTER),
            [('left', 'col-2'), ('center', 'col-10')],
        ),
        (
            (ProcessBodySection.CENTER, ProcessBodySection.RIGHT),
            [('center', 'col-10'), ('right', 'col-2')],
        ),
        (
            (ProcessBodySection.CENTER,),
            [('center', 'col-12')],
        ),
    ),
)
def test_process_layout_uses_fixed_bootstrap_geometry(roles, expected) -> None:
    layout = build_process_layout(
        _manifest(*roles),
        component_content=_content(*roles),
    )

    columns = _columns(layout)
    assert [(role, class_name.split()[0]) for role, class_name in columns] == expected


def test_process_layout_bottom_always_uses_twelve_columns() -> None:
    roles = (
        ProcessBodySection.LEFT,
        ProcessBodySection.CENTER,
        ProcessBodySection.RIGHT,
        ProcessBodySection.BOTTOM,
    )
    layout = build_process_layout(
        _manifest(*roles),
        component_content=_content(*roles),
    )
    bottom_row = _props(layout)['children'][1]
    bottom = _props(bottom_row)['children'][0]

    assert _props(bottom)['data-ada-process-component-key'] == 'indicadores_inferiores'
    assert _props(bottom)['data-ada-process-layout-role'] == 'bottom'
    assert _props(bottom)['className'].split()[0] == 'col-12'


def test_process_layout_wraps_each_role_in_one_component_container() -> None:
    manifest = _manifest(
        ProcessBodySection.LEFT,
        ProcessBodySection.CENTER,
        ProcessBodySection.RIGHT,
    )
    marker = html.Div('Injected', id='process-marker')
    content = _content(
        ProcessBodySection.LEFT,
        ProcessBodySection.CENTER,
        ProcessBodySection.RIGHT,
    )
    content['proceso_principal'] = marker

    layout = build_process_layout(
        manifest,
        component_content=content,
        layout_id='process-layout',
    )
    center_slot = _props(_props(layout)['children'][0])['children'][1]
    container = _props(center_slot)['children']
    container_content = _props(container)['children'][1]

    assert _props(layout)['id'] == 'process-layout'
    assert _props(center_slot)['data-ada-process-component-key'] == 'proceso_principal'
    assert _props(center_slot)['data-ada-process-layout-role'] == 'center'
    assert _props(container)['data-ada-component-key'] == 'proceso_principal'
    assert _props(_props(container)['children'][0])['children'] == 'Proceso Principal'
    assert _props(container_content)['children'] is marker


def test_process_layout_rejects_missing_component_content() -> None:
    manifest = _manifest(ProcessBodySection.LEFT, ProcessBodySection.CENTER)

    with pytest.raises(ProcessLayoutError, match='Missing process component content: aguas_arriba'):
        build_process_layout(
            manifest,
            component_content={'proceso_principal': html.Div('center')},
        )


def test_process_layout_rejects_unexpected_component_content() -> None:
    manifest = _manifest(ProcessBodySection.CENTER)

    with pytest.raises(ProcessLayoutError, match='Unexpected process component content: other'):
        build_process_layout(
            manifest,
            component_content={
                'proceso_principal': html.Div('center'),
                'other': html.Div('other'),
            },
        )
