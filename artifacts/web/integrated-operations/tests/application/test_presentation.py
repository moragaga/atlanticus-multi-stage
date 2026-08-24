from types import SimpleNamespace

from dash import html

import integrated_operations.application.presentation as presentation
from atlanticus.web.manager.web.ids import REFRESH_BUTTON_ID
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


def test_operational_route_uses_existing_operational_surface(monkeypatch) -> None:
    services = ServiceRegistry()
    operational = object()
    expected_tool = html.Div(id='operational-tool')
    composition = SimpleNamespace(operational=operational, manager=None)
    monkeypatch.setattr(
        presentation,
        'build_integrated_operations_tool',
        lambda value: expected_tool if value is operational else None,
    )

    surface = presentation.build_application_surface(
        services,
        composition=composition,
        pathname='/',
    )
    nodes = tuple(_walk(surface))

    assert _props(surface)['data-ada-unified-surface'] == 'operational'
    assert any(_props(node).get('id') == 'operational-tool' for node in nodes)


def test_manager_route_wraps_real_manager_surface_with_common_header(monkeypatch) -> None:
    services = ServiceRegistry()
    manager_content = html.Div(id='manager-content')
    manager_surface = SimpleNamespace(
        layout=lambda value: manager_content if value is services else None
    )
    composition = SimpleNamespace(
        operational=object(),
        manager=SimpleNamespace(surface=manager_surface),
    )
    monkeypatch.setattr(
        presentation, '_build_manager_header', lambda: html.Div(id='manager-header')
    )

    surface = presentation.build_application_surface(
        services,
        composition=composition,
        pathname='/manager/tools',
    )
    nodes = tuple(_walk(surface))

    assert _props(surface)['data-ada-unified-surface'] == 'manager'
    assert any(_props(node).get('id') == 'manager-header' for node in nodes)
    assert any(_props(node).get('id') == 'manager-content' for node in nodes)


def test_manager_header_keeps_navigation_and_refresh_action() -> None:
    nodes = tuple(_walk(presentation._build_manager_header()))
    ids = {_props(node).get('id') for node in nodes}

    assert REFRESH_BUTTON_ID in ids
    assert presentation._is_manager_route('/manager') is True
    assert presentation._is_manager_route('/manager/navigation') is True
    assert presentation._is_manager_route('/') is False


def test_manager_unavailable_does_not_replace_operational_baseline() -> None:
    surface = presentation.build_application_surface(
        ServiceRegistry(),
        composition=SimpleNamespace(operational=object(), manager=None),
        pathname='/manager',
    )

    assert _props(surface)['data-ada-unified-surface'] == 'manager-unavailable'
