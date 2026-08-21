# Registra una ruta Dash del Manager sin crear un segundo runtime Web.
from dash import html, register_page

register_page(__name__, path='/manager', name='Manager')

layout = html.Div()
