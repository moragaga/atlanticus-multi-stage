from ada.applications.reference.integrated_operations import (
    build_reference_integrated_operations_layout,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


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


def _find_by_id(component, component_id: str):
    return next(node for node in _walk(component) if _props(node).get('id') == component_id)


def test_reference_renders_integrated_operations_body_geometry_and_cards() -> None:
    section = build_reference_integrated_operations_layout()
    layout = _find_by_id(section, 'reference-integrated-operations-layout')
    scopes = _props(layout)['children']
    components = [
        component
        for scope in scopes
        for component in _props(scope)['children']
        if 'data-ada-component-key' in _props(component)
    ]
    component_keys = tuple(_props(component)['data-ada-component-key'] for component in components)
    cards = [
        item for item in _walk(layout) if _props(item).get('data-ada-component-card') == 'true'
    ]

    assert _props(layout)['data-ada-io-layout'] == 'integrated-operations'
    assert component_keys == (
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
    assert all(
        _props(component)['data-ada-component-container'] == 'true' for component in components
    )
    assert all(
        _props(_props(component)['children'][0])['children']
        == INTEGRATED_OPERATIONS_MANIFEST.section(
            _props(component)['data-ada-component-key']
        ).display_name
        for component in components
    )
    expected_card_keys = {
        child.key
        for component_key in component_keys
        for child in INTEGRATED_OPERATIONS_MANIFEST.children(component_key)
    }
    assert len(cards) == 22
    assert {_props(card)['data-ada-subcomponent-key'] for card in cards} == expected_card_keys
    assert all('flex-fill' in _props(card)['className'].split() for card in cards)


def test_reference_shared_carguio_transporte_card_has_no_component_title() -> None:
    section = build_reference_integrated_operations_layout()
    layout = _find_by_id(section, 'reference-integrated-operations-layout')
    mine = _props(layout)['children'][0]
    shared_wrapper = next(
        node
        for node in _props(mine)['children']
        if _props(node).get('data-ada-io-shared-subcomponent-key')
        == 'carguio_gestion_carguio_turno'
    )
    shared_card = _props(shared_wrapper)['children']

    assert _props(shared_card)['data-ada-component-card'] == 'true'
    assert _props(shared_card)['data-ada-subcomponent-key'] == 'carguio_gestion_carguio_turno'
    assert 'data-ada-component-container' not in _props(shared_wrapper)
