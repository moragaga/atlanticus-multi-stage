from dash import html

from ada.ui.components.state_wrapper import (
    ComponentCover,
    build_safe_state_wrapper,
    build_state_wrapper,
)


def _props(component):
    return component.to_plotly_json()['props']


def test_ready_wrapper_fills_parent_without_overlay() -> None:
    component = build_state_wrapper(
        content=html.Div('Contenido'),
        ready_name='demo-component',
    )
    props = _props(component)

    assert props['data-cover'] == 'none'
    assert props['data-ready'] == 'true'
    assert props['data-ready-name'] == 'demo-component'
    assert len(props['children']) == 1


def test_stale_wrapper_renders_overlay_above_content() -> None:
    component = build_state_wrapper(
        content=html.Div('Contenido'),
        cover=ComponentCover.stale(),
    )
    props = _props(component)
    overlay = props['children'][1]

    assert props['data-cover'] == 'stale'
    assert _props(overlay)['data-overlay-kind'] == 'stale'


def test_construction_wrapper_is_ready_without_content() -> None:
    component = build_state_wrapper(
        cover=ComponentCover.construction(),
        ready_name='future-component',
    )
    props = _props(component)

    assert props['data-cover'] == 'construction'
    assert props['data-ready'] == 'true'


def test_safe_wrapper_turns_isolated_failure_into_component_error() -> None:
    observed = []

    def broken():
        raise RuntimeError('boom')

    component = build_safe_state_wrapper(
        build_content=broken,
        ready_name='broken-component',
        on_error=observed.append,
    )
    props = _props(component)

    assert props['data-cover'] == 'component-error'
    assert props['data-ready'] == 'true'
    assert props['data-ready-name'] == 'broken-component'
    assert len(observed) == 1
