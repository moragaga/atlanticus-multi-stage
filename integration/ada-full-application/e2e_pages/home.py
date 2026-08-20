from dash import html, register_page

register_page(__name__, path='/', name='Inicio')

layout = html.Div('ADA Full Application E2E')
