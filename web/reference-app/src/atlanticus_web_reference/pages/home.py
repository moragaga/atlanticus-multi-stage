from dash import html, register_page

register_page(
    __name__,
    path='/',
    name='Home',
    title='Atlanticus Web',
    order=0,
)

layout = html.Section(
    [
        html.H1('Atlanticus Web'),
        html.P('Base web ejecutándose con Flask y Dash Pages.'),
    ],
    className='reference-page',
)
