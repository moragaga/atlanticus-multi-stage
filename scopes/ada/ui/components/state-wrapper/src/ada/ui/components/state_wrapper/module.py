from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_STATE_WRAPPER_ASSET_LAYER = AssetLayer(
    name='ada_ui_state_wrapper',
    load_order=210,
    package='ada.ui.components.state_wrapper',
)


def create_ada_state_wrapper_module() -> WebModule:
    return WebModule(
        name='ada-state-wrapper',
        asset_layers=(ADA_STATE_WRAPPER_ASSET_LAYER,),
    )
