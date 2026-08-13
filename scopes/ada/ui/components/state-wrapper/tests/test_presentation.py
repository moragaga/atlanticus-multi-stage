from dash import html
from dash.development.base_component import Component

from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper


def test_uncovered_wrapper_fills_parent_without_overlay() -> None:
    component = build_state_wrapper(content=html.Div('Contenido'))

    assert _prop(component, 'data-cover') == 'none'
    assert _prop(component, 'data-ready') == 'true'
    assert _find_by_class(component, 'ada-state-wrapper__overlay') is None


def test_stale_wrapper_renders_overlay_above_content() -> None:
    component = build_state_wrapper(
        content=html.Div('Contenido'),
        cover=ComponentCover.stale(),
    )

    overlay = _find_by_class(component, 'ada-state-wrapper__overlay--stale')
    assert overlay is not None
    assert _prop(component, 'data-cover') == 'stale'


def test_construction_wrapper_can_render_without_content_and_is_ready() -> None:
    component = build_state_wrapper(cover=ComponentCover.construction())

    overlay = _find_by_class(component, 'ada-state-wrapper__overlay--construction')
    assert overlay is not None
    assert _prop(component, 'data-ready') == 'true'


def test_dynamic_mount_can_start_pending_without_hidden_ready_flag() -> None:
    component = build_state_wrapper(
        content=html.Div('Pendiente'),
        ready=False,
        ready_name='global-indicators',
    )

    assert _prop(component, 'data-ready') == 'false'
    assert _prop(component, 'data-ready-name') == 'global-indicators'


def test_source_and_component_errors_are_controlled_ready_states() -> None:
    source_error = build_state_wrapper(cover=ComponentCover.source_error())
    component_error = build_state_wrapper(cover=ComponentCover.component_error())

    assert _prop(source_error, 'data-cover') == 'source_error'
    assert _prop(source_error, 'data-ready') == 'true'
    assert _prop(component_error, 'data-cover') == 'component_error'
    assert _prop(component_error, 'data-ready') == 'true'


def _find_by_class(component: Component, class_name: str) -> Component | None:
    classes = getattr(component, 'className', '') or ''
    if class_name in classes.split():
        return component
    children = getattr(component, 'children', None)
    if children is None:
        return None
    if not isinstance(children, (list, tuple)):
        children = [children]
    for child in children:
        if isinstance(child, Component):
            result = _find_by_class(child, class_name)
            if result is not None:
                return result
    return None


def _prop(component: Component, name: str):
    return component.to_plotly_json()['props'][name]
