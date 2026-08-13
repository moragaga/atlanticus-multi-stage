# Espejo comentado del renderer transversal de cobertura y readiness.
# Mantiene el mismo AST que la implementación productiva.
from __future__ import annotations

from collections.abc import Sequence

from dash import html
from dash.development.base_component import Component

from .models import ComponentCover

StateWrapperContent = Component | Sequence[Component] | None


def build_state_wrapper(
    *,
    content: StateWrapperContent = None,
    cover: ComponentCover | None = None,
    component_id: str | dict | None = None,
    class_name: str | None = None,
    ready: bool = True,
    ready_name: str | None = None,
) -> html.Div:
    resolved_cover = cover or ComponentCover.none()
    children: list[Component] = [
        html.Div(
            className='ada-state-wrapper__content',
            children=content,
        )
    ]
    overlay = _build_overlay(resolved_cover)
    if overlay is not None:
        children.append(overlay)

    properties = {
        'className': _join_classes('ada-state-wrapper', class_name),
        'data-cover': resolved_cover.state.value,
        'data-ready': 'true' if ready else 'false',
        'children': children,
    }
    if component_id is not None:
        properties['id'] = component_id
    if ready_name is not None:
        normalized_name = ready_name.strip()
        if normalized_name:
            properties['data-ready-name'] = normalized_name

    return html.Div(**properties)


def _build_overlay(cover: ComponentCover) -> html.Div | None:
    if not cover.covered:
        return None

    content: list[Component] = []
    if cover.icon_class is not None:
        content.append(
            html.I(
                className=f'{cover.icon_class} ada-state-wrapper__overlay-icon',
                **{'aria-hidden': 'true'},
            )
        )
    if cover.message is not None:
        content.append(
            html.P(
                cover.message,
                className='ada-state-wrapper__overlay-message',
            )
        )
    return html.Div(
        className=f'ada-state-wrapper__overlay ada-state-wrapper__overlay--{cover.state.value}',
        **{'data-overlay-kind': cover.state.value},
        children=[
            html.Div(
                className='ada-state-wrapper__overlay-content',
                children=content,
            )
        ],
    )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
