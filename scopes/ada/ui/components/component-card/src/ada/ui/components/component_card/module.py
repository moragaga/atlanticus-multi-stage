from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_COMPONENT_CARD_ASSET_LAYER = AssetLayer(
    name='ada_ui_component_card',
    load_order=230,
    package='ada.ui.components.component_card',
)


def create_ada_component_card_module() -> WebModule:
    return WebModule(
        name='ada-component-card',
        asset_layers=(ADA_COMPONENT_CARD_ASSET_LAYER,),
    )
