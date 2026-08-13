# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

from dash import html

from ada.ui.components.state_wrapper import ComponentCover, build_safe_state_wrapper

from .models import AlarmStatusState


# El wrapper de readiness se resuelve aquí para que Header sea solo un compositor de slots.
def build_alarm_status(
    state: AlarmStatusState | None,
    *,
    cover: ComponentCover | None = None,
) -> html.Div:
    return build_safe_state_wrapper(
        build_content=lambda: _build_content(state),
        cover=cover or ComponentCover.none(),
        ready_name='alarm-status',
    )


def _build_content(state: AlarmStatusState | None) -> html.Div | None:
    if state is None:
        return None
    return html.Div(
        className='ada-alarm-notifications-status',
        **{'data-section-key': 'alarm_status', 'data-scope': 'global'},
        children=[
            html.Div('Alarmas', className='ada-alarm-notifications-status__label'),
            _build_chip(label='Activas', count=state.active_count),
            _build_chip(label='Gestionadas', count=state.managed_count),
        ],
    )


def _build_chip(*, label: str, count: int) -> html.Div:
    return html.Div(
        className='ada-alarm-notifications-status__chip',
        children=[
            html.Span(str(count), className='ada-alarm-notifications-status__count'),
            html.Span(label, className='ada-alarm-notifications-status__text'),
        ],
    )
