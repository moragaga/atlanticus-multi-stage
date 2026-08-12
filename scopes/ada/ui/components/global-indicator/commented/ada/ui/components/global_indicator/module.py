# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_GLOBAL_INDICATOR_ASSET_LAYER = AssetLayer(
    name='ada_ui_global_indicator',
    load_order=225,
    package='ada.ui.components.global_indicator',
)


def create_ada_global_indicator_module() -> WebModule:
    return WebModule(
        name='ada-global-indicator',
        asset_layers=(ADA_GLOBAL_INDICATOR_ASSET_LAYER,),
    )
