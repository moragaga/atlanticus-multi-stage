from dash import html, register_page

register_page(__name__, path='/status', name='Status')

layout = html.Div(
    [
        html.H1('Status'),
        html.P('La navegación entre Pages mantiene el estado activo del menú.'),
    ],
    className='reference-ada__page',
)
