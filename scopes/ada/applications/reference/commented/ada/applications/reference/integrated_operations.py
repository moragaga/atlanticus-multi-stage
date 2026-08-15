# Espejo pedagógico: la reference app construye cards de demostración; el layout sigue recibiendo contenido ya construido.
from dash import html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.ui.components.component_card import build_component_card
from ada.ui.layouts.integrated_operations import build_integrated_operations_layout

_SHARED_COMPONENT = 'carguio'
_SHARED_SUBCOMPONENT = 'gestion_carguio_turno'


def build_reference_integrated_operations_layout() -> html.Section:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    component_content = {
        component.key: _build_component_cards(manifest, component.key)
        for scope_key in ('mine', 'plant')
        for component in manifest.children(scope_key)
    }
    shared_card = _build_shared_card(manifest)
    return html.Section(
        [
            html.H2('Integrated Operations Layout'),
            html.P(
                'ComponentCards reales del contrato IO con crecimiento determinado por su '
                'contenido y estructura estable para zoom Mina/Planta.'
            ),
            build_integrated_operations_layout(
                manifest,
                component_content=component_content,
                shared_card_content=shared_card,
                layout_id='reference-integrated-operations-layout',
            ),
        ],
        className='reference-ada__io-layout-demo',
    )


def _build_component_cards(manifest, component_key: str) -> html.Div:
    cards = []
    for section in manifest.children(component_key):
        if section.subcomponent is None or section.linked_component_keys:
            continue
        cards.append(
            build_component_card(
                manifest,
                component=component_key,
                subcomponent=section.subcomponent,
                content=html.Div(
                    'Contenido inyectado',
                    className='reference-ada__component-card-content',
                ),
                label=section.display_name,
                class_name='flex-fill',
            )
        )
    return html.Div(cards, className='d-flex flex-column gap-1')


def _build_shared_card(manifest):
    section = manifest.subcomponent(
        component='transporte',
        subcomponent=_SHARED_SUBCOMPONENT,
    )
    return build_component_card(
        manifest,
        component=_SHARED_COMPONENT,
        subcomponent=_SHARED_SUBCOMPONENT,
        content=html.Div(
            'Contenido inyectado',
            className='reference-ada__component-card-content',
        ),
        label=section.display_name,
        class_name='flex-fill',
    )
