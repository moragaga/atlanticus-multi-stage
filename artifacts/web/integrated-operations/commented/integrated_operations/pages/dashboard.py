# Dash Pages mantiene registrada la ruta raíz, mientras el layout real de la aplicación se compone con la proyección resuelta.
from dash import html, register_page

register_page(__name__, path='/', name='Integrated Operations')

layout = html.Div()
