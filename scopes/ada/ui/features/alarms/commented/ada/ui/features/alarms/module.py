# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

# La feature publica una sola capa de assets; las subfronteras siguen dentro del mismo paquete.
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
