from dash import html, register_page

from ada.ui.framework.core import ready_attributes

register_page(__name__, path='/status', name='Status')

layout = html.Div(
    [
        html.H1('Status'),
        html.P('La navegación entre Pages mantiene el estado activo del menú.'),
    ],
    className='reference-ada__page',
    **ready_attributes('page-content', ready=True),
)
