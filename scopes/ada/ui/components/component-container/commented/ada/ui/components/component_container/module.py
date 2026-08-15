from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

# Se carga antes de ComponentCard para que la primitiva exterior esté disponible primero.
ADA_COMPONENT_CONTAINER_ASSET_LAYER = AssetLayer(
    name='ada_ui_component_container',
    load_order=226,
    package='ada.ui.components.component_container',
)


def create_ada_component_container_module() -> WebModule:
    return WebModule(
        name='ada-component-container',
        asset_layers=(ADA_COMPONENT_CONTAINER_ASSET_LAYER,),
    )
