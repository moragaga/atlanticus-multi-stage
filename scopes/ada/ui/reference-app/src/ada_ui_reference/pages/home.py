from dash import html, register_page

from ada.ui.components.state_wrapper import (
    ComponentCover,
    build_safe_state_wrapper,
    build_state_wrapper,
)
from ada.ui.core import ready_attributes

register_page(__name__, path='/', name='Inicio')


def _broken_component():
    raise RuntimeError('Reference component failure')


layout = html.Div(
    [
        html.H1('ADA UI Resilience'),
        html.P('Referencia visual de estados controlados sin alterar la geometría.'),
        html.Div(
            className='reference-ada__resilience-grid',
            children=[
                build_state_wrapper(
                    content=html.Div('Contenido stale', className='reference-ada__demo-content'),
                    cover=ComponentCover.stale(),
                ),
                build_state_wrapper(
                    content=html.Div(
                        'Contenido de fuente',
                        className='reference-ada__demo-content',
                    ),
                    cover=ComponentCover.source_error(),
                ),
                build_state_wrapper(
                    content=html.Div('Módulo futuro', className='reference-ada__demo-content'),
                    cover=ComponentCover.construction(),
                ),
                build_safe_state_wrapper(
                    build_content=_broken_component,
                ),
            ],
        ),
    ],
    className='reference-ada__page',
    **ready_attributes('page-content', ready=True),
)
