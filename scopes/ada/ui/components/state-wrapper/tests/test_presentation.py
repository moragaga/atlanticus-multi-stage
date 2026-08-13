from dash import html
from dash.development.base_component import Component

from ada.ui.components.state_wrapper import StateWrapperState, build_state_wrapper


def test_ready_wrapper_fills_parent_without_overlay() -> None:
    component = build_state_wrapper(content=html.Div('Contenido'))

    assert _prop(component, 'data-availability') == 'ready'
    assert _prop(component, 'data-freshness') == 'fresh'
    assert _find_by_class(component, 'ada-state-wrapper__overlay') is None


def test_stale_wrapper_renders_overlay_above_content() -> None:
    component = build_state_wrapper(
        content=html.Div('Contenido'),
        state=StateWrapperState.stale(),
    )

    overlay = _find_by_class(component, 'ada-state-wrapper__overlay--stale')
    assert overlay is not None
    assert _prop(component, 'data-freshness') == 'stale'


def test_construction_wrapper_can_render_without_content() -> None:
    component = build_state_wrapper(state=StateWrapperState.construction())

    overlay = _find_by_class(component, 'ada-state-wrapper__overlay--construction')
    assert overlay is not None
    assert _prop(component, 'data-availability') == 'construction'


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
