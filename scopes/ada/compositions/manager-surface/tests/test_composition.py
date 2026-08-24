from types import SimpleNamespace

import pytest
from dash import html, no_update

from ada.compositions.manager_surface import create_ada_manager_surface_composition
from atlanticus.web.services import ServiceRegistry


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


def _surface(*, route_prefix: str = '/manager'):
    return SimpleNamespace(
        definition=SimpleNamespace(route_prefix=route_prefix),
        web_modules=('manager-workflows', 'manager-callbacks'),
        layout=lambda services: html.Div(
            'manager-body',
            id='manager-body',
            **{'data-service-registry': str(id(services))},
        ),
    )


def test_manager_surface_composition_owns_embedded_presentation() -> None:
    services = ServiceRegistry()
    composition = create_ada_manager_surface_composition(
        surface=_surface(),
        principal_binding='manager-principal',
    )

    rendered = composition.build(services)
    nodes = tuple(_walk(rendered))
    ids = {_props(node).get('id') for node in nodes}

    assert composition.route_prefix == '/manager'
    assert composition.matches('/manager') is True
    assert composition.matches('/manager/tools') is True
    assert composition.matches('/') is False
    assert composition.web_modules[:-1] == (
        'manager-principal',
        'manager-workflows',
        'manager-callbacks',
    )
    assert composition.web_modules[-1].name == 'ada-manager-surface-presentation'
    assert composition.web_modules[-1].asset_layers[0].name == 'ada_manager_surface'
    assert _props(rendered)['data-ada-manager-surface'] == 'true'
    assert _props(rendered)['data-ada-unified-surface'] == 'manager'
    assert 'atlanticus-manager-refresh' in ids
    assert 'app-header-desktop-toggle' in ids
    assert 'app-header-mobile-toggle' in ids
    assert 'manager-body' in ids


def test_manager_surface_composition_requires_embedded_route_prefix() -> None:
    with pytest.raises(ValueError, match='requires a route prefix'):
        create_ada_manager_surface_composition(
            surface=_surface(route_prefix=''),
            principal_binding='manager-principal',
        )


def test_manager_surface_presentation_refresh_callback_preserves_contract() -> None:
    composition = create_ada_manager_surface_composition(
        surface=_surface(),
        principal_binding='manager-principal',
    )
    callback = composition.presentation_module.register_callbacks
    assert callback is not None

    registered = []

    class FakeApp:
        def callback(self, *_args, **_kwargs):
            def decorator(function):
                registered.append(function)
                return function

            return decorator

    callback(FakeApp(), ServiceRegistry())

    assert len(registered) == 1
    assert registered[0](None, 4) is no_update
    assert registered[0](0, 4) is no_update
    assert registered[0](1, None) == 1
    assert registered[0](2, 4) == 5
