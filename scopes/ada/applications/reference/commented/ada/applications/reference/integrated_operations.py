from dash import html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.ui.layouts.integrated_operations import build_integrated_operations_layout


# La aplicación de referencia demuestra la frontera: ella construye el contenido y el layout solo lo posiciona.
def build_reference_integrated_operations_layout() -> html.Section:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    # Los placeholders son contenido de la herramienta; no forman parte del módulo de layout.
    component_content = {
        section.key: html.Div(
            [
                html.Strong(section.display_name),
                html.Span('Contenido inyectado por la herramienta'),
            ],
            className='reference-ada__io-placeholder',
        )
        for scope_key in ('mine', 'plant')
        for section in manifest.children(scope_key)
    }
    return html.Section(
        [
            html.H2('Integrated Operations Layout'),
            html.P(
                'Geometría semántica con contenido inyectado y estructura estable para '
                'zoom Mina/Planta.'
            ),
            build_integrated_operations_layout(
                manifest,
                component_content=component_content,
                layout_id='reference-integrated-operations-layout',
            ),
        ],
        className='reference-ada__io-layout-demo',
    )
