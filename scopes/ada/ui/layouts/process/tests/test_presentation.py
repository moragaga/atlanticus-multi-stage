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
_KPI_ALARM = frozenset({ToolTarget.KPI, ToolTarget.ALARM})
_FUNCTIONAL_KEYS = {
    ProcessBodySection.LEFT: 'aguas_arriba',
    ProcessBodySection.CENTER: 'proceso_principal',
    ProcessBodySection.RIGHT: 'aguas_abajo',
    ProcessBodySection.BOTTOM: 'indicadores_inferiores',
}


def _region(role: ProcessBodySection) -> ToolSection:
    key = _FUNCTIONAL_KEYS[role]
    return ToolSection(
        key=key,
        display_name=key.replace('_', ' ').title(),
        kind=ToolSectionKind.REGION,
        scope=ToolScope.PLANT,
        parent_key='body',
        targets=_KPI_ALARM if role is ProcessBodySection.CENTER else _KPI,
        layout_role=role,
    )


def _manifest(*roles: ProcessBodySection):
    return build_process_manifest(
        tool_key='process_reference',
        display_name='Process Reference',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=tuple(_region(role) for role in roles),
    )


def _content(*roles: ProcessBodySection):
    return {_FUNCTIONAL_KEYS[role]: html.Div(role.value) for role in roles}


def _props(component):
    return component.to_plotly_json()['props']


def _columns(layout):
    main = _props(layout)['children'][0]
    return [
        (_props(region)['data-ada-process-layout-role'], _props(region)['className'])
        for region in _props(main)['children']
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
    manifest = _manifest(*roles)

    layout = build_process_layout(manifest, region_content=_content(*roles))

    columns = _columns(layout)
    assert [(role, class_name.split()[0]) for role, class_name in columns] == expected


def test_process_layout_bottom_always_uses_twelve_columns() -> None:
    roles = (
        ProcessBodySection.LEFT,
        ProcessBodySection.CENTER,
        ProcessBodySection.RIGHT,
        ProcessBodySection.BOTTOM,
    )
    manifest = _manifest(*roles)
    layout = build_process_layout(manifest, region_content=_content(*roles))
    bottom_row = _props(layout)['children'][1]
    bottom = _props(bottom_row)['children'][0]

    assert _props(bottom)['data-ada-process-region-key'] == 'indicadores_inferiores'
    assert _props(bottom)['data-ada-process-layout-role'] == 'bottom'
    assert _props(bottom)['className'].split()[0] == 'col-12'


def test_process_layout_preserves_functional_region_identity_and_content() -> None:
    center = ToolSection(
        key='planta_molibdeno',
        display_name='Planta Molibdeno',
        kind=ToolSectionKind.REGION,
        scope=ToolScope.PLANT,
        parent_key='body',
        targets=_KPI_ALARM,
        layout_role=ProcessBodySection.CENTER,
    )
    manifest = build_process_manifest(
        tool_key='flotacion_selectiva',
        display_name='Flotación Selectiva',
        sources=(_PI,),
        operational_scope=ToolScope.PLANT,
        body_sections=(center,),
    )
    marker = html.Div('Injected', id='process-marker')

    layout = build_process_layout(
        manifest,
        region_content={'planta_molibdeno': marker},
        layout_id='process-layout',
    )
    region = _props(_props(layout)['children'][0])['children'][0]
    region_content = _props(region)['children'][1]

    assert _props(layout)['id'] == 'process-layout'
    assert _props(region)['data-ada-process-region-key'] == 'planta_molibdeno'
    assert _props(region)['data-ada-process-layout-role'] == 'center'
    assert _props(region_content)['children'] is marker


def test_process_layout_rejects_missing_region_content() -> None:
    manifest = _manifest(ProcessBodySection.LEFT, ProcessBodySection.CENTER)

    with pytest.raises(ProcessLayoutError, match='Missing process region content: aguas_arriba'):
        build_process_layout(
            manifest,
            region_content={'proceso_principal': html.Div('center')},
        )


def test_process_layout_rejects_unexpected_region_content() -> None:
    manifest = _manifest(ProcessBodySection.CENTER)

    with pytest.raises(ProcessLayoutError, match='Unexpected process region content: other'):
        build_process_layout(
            manifest,
            region_content={
                'proceso_principal': html.Div('center'),
                'other': html.Div('other'),
            },
        )
