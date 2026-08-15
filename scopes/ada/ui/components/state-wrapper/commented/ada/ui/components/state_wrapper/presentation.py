# Espejo comentado del wrapper transversal y de su overlay reutilizable en callbacks dinámicos.
from __future__ import annotations

from collections.abc import Callable, Sequence

from dash import html
from dash.development.base_component import Component

from .models import ComponentCover, normalize_ready_name

StateWrapperContent = Component | Sequence[Component] | None


# Construye el boundary estable que conserva el contenido aunque cambie su estado visual.
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
    overlay = build_state_overlay(resolved_cover)
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
        properties['data-ready-name'] = normalize_ready_name(ready_name)

    return html.Div(**properties)


# Convierte una excepción local del renderer en un error aislado del componente.
def build_safe_state_wrapper(
    *,
    build_content: Callable[[], StateWrapperContent],
    cover: ComponentCover | None = None,
    component_id: str | dict | None = None,
    class_name: str | None = None,
    ready_name: str | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> html.Div:
    try:
        content = build_content()
    except Exception as exc:
        if on_error is not None:
            try:
                on_error(exc)
            except Exception:
                pass
        return build_state_wrapper(
            cover=ComponentCover.component_error(),
            component_id=component_id,
            class_name=class_name,
            ready=True,
            ready_name=ready_name,
        )
    return build_state_wrapper(
        content=content,
        cover=cover,
        component_id=component_id,
        class_name=class_name,
        ready=True,
        ready_name=ready_name,
    )


# Expone solo el overlay para que Dashboard pueda actualizar estado sin reconstruir el contenido.
def build_state_overlay(cover: ComponentCover) -> html.Div | None:
    if not isinstance(cover, ComponentCover):
        raise TypeError('State overlay requires ComponentCover')
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
