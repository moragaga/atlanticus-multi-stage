# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_HEADER_ASSET_LAYER = AssetLayer(
    name='ada_ui_header',
    load_order=250,
    package='ada.ui.shell.header',
)


def create_ada_header_module() -> WebModule:
    return WebModule(
        name='ada-header',
        asset_layers=(ADA_HEADER_ASSET_LAYER,),
    )
