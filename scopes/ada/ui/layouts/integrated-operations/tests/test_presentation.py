from dataclasses import replace

from dash import html

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolScope,
    ToolSection,
    ToolSectionKind,
)
from ada.ui.layouts.integrated_operations import (
    IntegratedOperationsLayoutError,
    IntegratedOperationsView,
    build_integrated_operations_layout,
)

_COMPONENT_KEYS = (
    'general_mina',
    'carguio',
    'transporte',
    'chancado_stmg',
    'stockpile_chacay',
    'molienda',
    'flotacion',
    'transporte_fluidos',
    'puerto',
)


def _props(component):
    return component.to_plotly_json()['props']


def _content():
    return {key: html.Div(key) for key in _COMPONENT_KEYS}


def _shared_card():
    return html.Div('shared-card', id='shared-card')


def _component_keys(layout):
    root_props = _props(layout)
    scopes = root_props['children']
    return tuple(
        _props(component)['data-ada-component-key']
        for scope in scopes
        for component in _props(scope)['children']
        if 'data-ada-component-key' in _props(component)
    )


def test_overview_preserves_semantic_scope_and_component_identities() -> None:
    layout = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=_shared_card(),
        layout_id='io-layout',
    )
    props = _props(layout)
    mine, plant = props['children']

    assert props['id'] == 'io-layout'
    assert props['data-ada-io-layout'] == 'integrated-operations'
    assert props['data-ada-io-view'] == 'overview'
    assert _props(mine)['data-ada-io-scope-key'] == 'mine'
    assert _props(plant)['data-ada-io-scope-key'] == 'plant'
    assert _component_keys(layout) == _COMPONENT_KEYS


def test_layout_omits_optional_id_when_not_provided() -> None:
    layout = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=_shared_card(),
    )

    assert 'id' not in _props(layout)


def test_zoom_views_keep_the_same_component_tree() -> None:
    overview = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=_shared_card(),
    )
    mine = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=_shared_card(),
        view=IntegratedOperationsView.MINE,
    )
    plant = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=_shared_card(),
        view=IntegratedOperationsView.PLANT,
    )

    assert _component_keys(overview) == _component_keys(mine) == _component_keys(plant)
    assert _props(mine)['data-ada-io-view'] == 'mine'
    assert _props(plant)['data-ada-io-view'] == 'plant'


def test_layout_renders_injected_content_without_rewriting_it() -> None:
    marker = html.Div('Injected', id='injected-marker')
    content = _content()
    content['flotacion'] = marker

    layout = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=content,
        shared_card_content=_shared_card(),
    )
    flotation = next(
        component
        for scope in _props(layout)['children']
        for component in _props(scope)['children']
        if _props(component).get('data-ada-component-key') == 'flotacion'
    )

    content_wrapper = _props(flotation)['children'][1]
    assert _props(content_wrapper)['children'] is marker


def test_layout_rejects_missing_component_content() -> None:
    content = _content()
    del content['molienda']

    try:
        build_integrated_operations_layout(
            INTEGRATED_OPERATIONS_MANIFEST,
            component_content=content,
            shared_card_content=_shared_card(),
        )
    except IntegratedOperationsLayoutError as exc:
        assert str(exc) == 'Missing integrated operations component content: molienda'
    else:
        raise AssertionError('Expected missing content validation error')


def test_layout_rejects_unexpected_component_content() -> None:
    content = _content()
    content['unknown'] = html.Div('Unknown')

    try:
        build_integrated_operations_layout(
            INTEGRATED_OPERATIONS_MANIFEST,
            component_content=content,
            shared_card_content=_shared_card(),
        )
    except IntegratedOperationsLayoutError as exc:
        assert str(exc) == 'Unexpected integrated operations component content: unknown'
    else:
        raise AssertionError('Expected unexpected content validation error')


def test_layout_rejects_manifest_components_outside_fixed_geometry() -> None:
    extra = ToolSection(
        key='extra_component',
        display_name='Extra Component',
        kind=ToolSectionKind.COMPONENT,
        scope=ToolScope.PLANT,
        parent_key='plant',
    )
    manifest = replace(
        INTEGRATED_OPERATIONS_MANIFEST,
        sections=(*INTEGRATED_OPERATIONS_MANIFEST.sections, extra),
    )

    try:
        build_integrated_operations_layout(
            manifest,
            component_content=_content(),
            shared_card_content=_shared_card(),
        )
    except IntegratedOperationsLayoutError as exc:
        assert str(exc) == "Region 'plant' does not match integrated operations geometry"
    else:
        raise AssertionError('Expected fixed geometry validation error')


def test_shared_carguio_transporte_card_spans_without_component_container() -> None:
    shared = _shared_card()
    layout = build_integrated_operations_layout(
        INTEGRATED_OPERATIONS_MANIFEST,
        component_content=_content(),
        shared_card_content=shared,
    )
    mine = _props(layout)['children'][0]
    nodes = _props(mine)['children']
    shared_wrapper = next(
        node
        for node in nodes
        if _props(node).get('data-ada-io-shared-subcomponent-key')
        == 'carguio_gestion_carguio_turno'
    )

    assert 'data-ada-component-key' not in _props(shared_wrapper)
    assert _props(shared_wrapper)['children'] is shared
    assert 'ada-io-layout__shared-card--carguio-transporte' in _props(shared_wrapper)['className']
