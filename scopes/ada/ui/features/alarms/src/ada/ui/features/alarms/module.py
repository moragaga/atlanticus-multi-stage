from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_ALARMS_ASSET_LAYER = AssetLayer(
    name='ada_ui_alarms',
    load_order=260,
    package='ada.ui.features.alarms',
)


def create_ada_alarms_module() -> WebModule:
    return WebModule(
        name='ada-alarms',
        asset_layers=(ADA_ALARMS_ASSET_LAYER,),
    )
