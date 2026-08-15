# El módulo registra únicamente los assets visuales del layout y no depende del motor de alarmas.
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_INTEGRATED_OPERATIONS_LAYOUT_ASSET_LAYER = AssetLayer(
    name='ada_ui_layout_integrated_operations',
    load_order=240,
    package='ada.ui.layouts.integrated_operations',
)


def create_ada_integrated_operations_layout_module() -> WebModule:
    return WebModule(
        name='ada-integrated-operations-layout',
        asset_layers=(ADA_INTEGRATED_OPERATIONS_LAYOUT_ASSET_LAYER,),
    )
