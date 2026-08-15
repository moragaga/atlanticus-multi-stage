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


def test_reference_renders_all_integrated_operations_components_and_cards() -> None:
    section = build_reference_integrated_operations_layout()
    layout = _props(section)['children'][2]
    scopes = _props(layout)['children']
    component_keys = tuple(
        _props(component)['data-ada-component-key']
        for scope in scopes
        for component in _props(scope)['children']
    )
    cards = [
        item for item in _walk(layout) if _props(item).get('data-ada-component-card') == 'true'
    ]

    assert _props(layout)['id'] == 'reference-integrated-operations-layout'
    assert _props(layout)['data-ada-io-view'] == 'overview'
    assert component_keys == (
        'general_mina',
        'carguio',
        'transporte',
        'carguio_transporte',
        'chancado_stmg',
        'stockpile_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    )
    expected_card_keys = {
        child.key
        for component_key in component_keys
        for child in INTEGRATED_OPERATIONS_MANIFEST.children(component_key)
    }
    assert len(cards) == 22
    assert {_props(card)['data-ada-subcomponent-key'] for card in cards} == expected_card_keys
    assert all('flex-fill' in _props(card)['className'].split() for card in cards)
