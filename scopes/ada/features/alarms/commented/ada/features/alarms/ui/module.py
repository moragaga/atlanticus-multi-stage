# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

ADA_ALARMS_ASSET_LAYER = AssetLayer(
    name='ada_ui_alarms',
    load_order=260,
    package='ada.features.alarms.ui',
)


def create_ada_alarms_module() -> WebModule:
    return WebModule(
        name='ada-alarms',
        asset_layers=(ADA_ALARMS_ASSET_LAYER,),
    )
