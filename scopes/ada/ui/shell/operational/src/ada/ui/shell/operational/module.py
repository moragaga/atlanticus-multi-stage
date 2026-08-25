from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_OPERATIONAL_SHELL_ASSET_LAYER = AssetLayer(
    name='ada_ui_operational_shell',
    load_order=255,
    package='ada.ui.shell.operational',
)


def create_ada_operational_shell_module() -> WebModule:
    return WebModule(
        name='ada-operational-shell',
        asset_layers=(ADA_OPERATIONAL_SHELL_ASSET_LAYER,),
    )
