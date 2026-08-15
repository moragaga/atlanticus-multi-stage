from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_PROCESS_LAYOUT_ASSET_LAYER = AssetLayer(
    name='ada_ui_layout_process',
    load_order=241,
    package='ada.ui.layouts.process',
)


def create_ada_process_layout_module() -> WebModule:
    return WebModule(
        name='ada-process-layout',
        asset_layers=(ADA_PROCESS_LAYOUT_ASSET_LAYER,),
    )
