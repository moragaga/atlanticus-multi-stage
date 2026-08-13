from __future__ import annotations

from ada.ui.navigation.callbacks import register_ada_navigation_callbacks
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_NAVIGATION_ASSET_LAYER = AssetLayer(
    name='ada_ui_navigation',
    load_order=200,
    package='ada.ui.navigation',
)


def create_ada_navigation_module() -> WebModule:
    return WebModule(
        name='ada-navigation',
        asset_layers=(ADA_NAVIGATION_ASSET_LAYER,),
        register_callbacks=register_ada_navigation_callbacks,
    )
