# Espejo comentado de pages/home.py.
from dash import html, register_page

register_page(__name__, path='/', name='Inicio')

layout = html.Div(
    [
        html.H1('ADA UI Navigation'),
        html.P('Referencia visual aislada del menú ADA aprobado.'),
    ],
    className='reference-ada__page',
)
