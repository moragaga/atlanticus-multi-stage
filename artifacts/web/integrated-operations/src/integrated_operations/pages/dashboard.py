from dash import register_page

from integrated_operations.tool import build_integrated_operations_tool

register_page(__name__, path='/', name='Integrated Operations')

layout = build_integrated_operations_tool
