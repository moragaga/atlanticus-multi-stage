from types import SimpleNamespace

from dash import html

import integrated_operations.application.presentation as presentation
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


def test_unified_layout_has_one_dynamic_surface_host_and_navigation(monkeypatch) -> None:
    services = ServiceRegistry()
    composition = SimpleNamespace()
    navigation = html.Div(id='navigation-overlay')
    monkeypatch.setattr(
        presentation,
        'build_ada_navigation_offcanvas_from_services',
        lambda value: navigation if value is services else None,
    )
    monkeypatch.setattr(
        presentation,
        'build_application_surface',
        lambda value, *, composition, pathname: (
            html.Div(id='initial-operational') if value is services and pathname == '/' else None
        ),
    )

    layout = presentation.build_unified_application_layout(
        services,
        composition=composition,
    )
    nodes = tuple(_walk(layout))

    assert _props(layout)['data-ada-unified-application'] == 'true'
    assert sum(_props(node).get('id') == presentation.LOCATION_ID for node in nodes) == 1
    assert sum(_props(node).get('id') == presentation.SURFACE_HOST_ID for node in nodes) == 1
    assert sum(_props(node).get('id') == 'navigation-overlay' for node in nodes) == 1
    assert sum(_props(node).get('id') == 'initial-operational' for node in nodes) == 1


def test_operational_route_uses_registered_surface_adapter() -> None:
    services = ServiceRegistry()
    expected = html.Div(id='operational-tool')
    operational = SimpleNamespace(
        adapter_key='integrated_operations',
        build=lambda value: expected if value is services else None,
    )
    composition = SimpleNamespace(operational=operational, manager=None)

    surface = presentation.build_application_surface(
        services,
        composition=composition,
        pathname='/',
    )
    nodes = tuple(_walk(surface))

    assert _props(surface)['data-ada-unified-surface'] == 'operational'
    assert _props(surface)['data-ada-surface-adapter'] == 'integrated_operations'
    assert any(_props(node).get('id') == 'operational-tool' for node in nodes)


def test_manager_route_delegates_complete_presentation_to_manager_composition() -> None:
    services = ServiceRegistry()
    expected = html.Div(id='manager-composition')
    captured = []

    def build(value):
        captured.append(value)
        return expected

    manager = SimpleNamespace(
        build=build,
        matches=lambda pathname: pathname == '/manager/tools',
    )
    composition = SimpleNamespace(operational=object(), manager=manager)

    surface = presentation.build_application_surface(
        services,
        composition=composition,
        pathname='/manager/tools',
    )

    assert surface is expected
    assert captured == [services]


def test_manager_route_contract_keeps_deep_links() -> None:
    assert presentation._is_manager_route('/manager') is True
    assert presentation._is_manager_route('/manager/tools') is True
    assert presentation._is_manager_route('/manager/users') is True
    assert presentation._is_manager_route('/manager/navigation') is True
    assert presentation._is_manager_route('/') is False


def test_manager_unavailable_does_not_replace_operational_baseline() -> None:
    surface = presentation.build_application_surface(
        ServiceRegistry(),
        composition=SimpleNamespace(operational=object(), manager=None),
        pathname='/manager',
    )

    props = _props(surface)
    assert props['data-ada-unified-surface'] == 'manager-unavailable'
    assert 'Volver a la aplicación' in str(props['children'])
