# Aplicación de referencia: demuestra el contrato web sin introducir lógica de negocio real.
from dash import html, register_page

register_page(
    __name__,
    path='/status',
    name='Status',
    title='Atlanticus Web · Status',
    order=1,
)

layout = html.Section(
    [
        html.H1('Status'),
        html.P('Página descubierta e importada dinámicamente.'),
    ],
    className='reference-page',
)
