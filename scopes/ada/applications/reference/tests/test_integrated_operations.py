from ada.applications.reference.integrated_operations import (
    build_reference_integrated_operations_layout,
)


def _props(component):
    return component.to_plotly_json()['props']


def test_reference_injects_content_into_integrated_operations_layout() -> None:
    section = build_reference_integrated_operations_layout()
    layout = _props(section)['children'][2]
    scopes = _props(layout)['children']
    component_keys = tuple(
        _props(component)['data-ada-component-key']
        for scope in scopes
        for component in _props(scope)['children']
    )

    assert _props(layout)['id'] == 'reference-integrated-operations-layout'
    assert _props(layout)['data-ada-io-view'] == 'overview'
    assert component_keys == (
        'general_mina',
        'carguio',
        'transporte',
        'carguio_transporte',
        'chancado_stmg',
        'stock_chacay',
        'molienda',
        'flotacion',
        'transporte_fluidos',
        'puerto',
    )
