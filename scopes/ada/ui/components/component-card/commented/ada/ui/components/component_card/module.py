from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

# ComponentCard se carga después de los componentes base y antes de los layouts ADA.
ADA_COMPONENT_CARD_ASSET_LAYER = AssetLayer(
    name='ada_ui_component_card',
    load_order=230,
    package='ada.ui.components.component_card',
)


def create_ada_component_card_module() -> WebModule:
    # El módulo solo publica sus assets; no registra callbacks ni runtime.
    return WebModule(
        name='ada-component-card',
        asset_layers=(ADA_COMPONENT_CARD_ASSET_LAYER,),
    )
