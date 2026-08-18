from __future__ import annotations

from dash import html

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.features.dashboard import DashboardMount
from ada.ui.components.component_card import build_component_card
from ada.ui.layouts.integrated_operations import build_integrated_operations_layout

_SHARED_COMPONENT = 'carguio'
_SHARED_SUBCOMPONENT = 'gestion_carguio_turno'


def build_reference_integrated_operations_layout(
    *,
    mount: DashboardMount | None = None,
) -> html.Section:
    manifest = INTEGRATED_OPERATIONS_MANIFEST
    component_content = {
        component.key: _build_component_cards(
            manifest,
            component.key,
            mount=mount,
        )
        for scope_key in ('mine', 'plant')
        for component in manifest.children(scope_key)
    }
    layout = build_integrated_operations_layout(
        manifest,
        component_content=component_content,
        shared_card_content=_build_shared_card(manifest),
        layout_id='reference-integrated-operations-layout',
    )
    children = [
        html.H2('Integrated Operations Layout'),
        html.P(
            'Geometría estable del body de Operaciones Integradas. La composición completa '
            'se certificará fuera de la aplicación reference.'
        ),
        layout,
    ]
    if mount is not None:
        children.append(mount.runtime_host())
    return html.Section(
        children,
        className='reference-ada__io-layout-demo',
    )


def _build_component_cards(
    manifest,
    component_key: str,
    *,
    mount: DashboardMount | None,
) -> html.Div:
    cards = []
    for section in manifest.children(component_key):
        if section.subcomponent is None or section.linked_component_keys:
            continue
        slot = mount.slot(component_key, section.subcomponent) if mount is not None else None
        cards.append(
            build_component_card(
                manifest,
                component=component_key,
                subcomponent=section.subcomponent,
                content=(
                    slot.content
                    if slot is not None
                    else html.Div(
                        'Contenido inyectado',
                        className='reference-ada__component-card-content',
                    )
                ),
                label=section.display_name,
                overlay=slot.overlay if slot is not None else None,
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
            'Slot compartido específico IO',
            className='reference-ada__component-card-content',
        ),
        label=section.display_name,
        class_name='flex-fill',
    )
