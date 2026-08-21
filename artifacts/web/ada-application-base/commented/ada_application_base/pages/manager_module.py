# Registra una ruta Dash del Manager sin crear un segundo runtime Web.
from dash import html, register_page

register_page(
    __name__,
    path_template='/manager/<module>',
    name='Manager module',
)


def layout(module: str | None = None, **_kwargs):
    del module
    return html.Div()
