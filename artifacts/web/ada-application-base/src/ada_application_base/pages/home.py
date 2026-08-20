from dash import html, register_page

register_page(__name__, path='/', name='Inicio')

layout = html.Main(
    html.Div('ADA', className='ada-application-base__title'),
    className='ada-application-base',
)
