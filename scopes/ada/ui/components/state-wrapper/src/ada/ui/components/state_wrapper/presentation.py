from __future__ import annotations

from collections.abc import Sequence

from dash import html
from dash.development.base_component import Component

from .models import StateWrapperState

StateWrapperContent = Component | Sequence[Component] | None


def build_state_wrapper(
    *,
    content: StateWrapperContent = None,
    state: StateWrapperState | None = None,
    component_id: str | dict | None = None,
    class_name: str | None = None,
) -> html.Div:
    resolved_state = state or StateWrapperState.ready()
    children: list[Component] = [
        html.Div(
            className='ada-state-wrapper__content',
            children=content,
        )
    ]
    overlay = _build_overlay(resolved_state)
    if overlay is not None:
        children.append(overlay)

    properties = {
        'className': _join_classes('ada-state-wrapper', class_name),
        'data-availability': resolved_state.availability.value,
        'data-freshness': resolved_state.freshness.value,
        'children': children,
    }
    if component_id is not None:
        properties['id'] = component_id

    return html.Div(**properties)


def _build_overlay(state: StateWrapperState) -> html.Div | None:
    if not state.has_overlay:
        return None
    kind = state.overlay_kind
    if kind is None:
        return None
    content: list[Component] = []
    if state.icon_class is not None:
        content.append(
            html.I(
                className=f'{state.icon_class} ada-state-wrapper__overlay-icon',
                **{'aria-hidden': 'true'},
            )
        )
    if state.message is not None:
        content.append(
            html.P(
                state.message,
                className='ada-state-wrapper__overlay-message',
            )
        )
    return html.Div(
        className=f'ada-state-wrapper__overlay ada-state-wrapper__overlay--{kind}',
        **{'data-overlay-kind': kind},
        children=[
            html.Div(
                className='ada-state-wrapper__overlay-content',
                children=content,
            )
        ],
    )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
