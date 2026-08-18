# Espejo comentado: la página raíz solo monta la herramienta ya compuesta.
from dash import register_page

from process_base.tool import build_process_base_tool

register_page(__name__, path='/', name='Process Base')

layout = build_process_base_tool
