# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Configuración de herramientas del scope ADA. Convierte datos administrativos mínimos en contratos runtime ToolManifest sin acoplar el dominio a la UI.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule

from ada.configuration.tools.web.callbacks import register_tool_admin_callbacks
from ada.configuration.tools.web.models import ToolAdminWebContext


def create_tool_admin_web_module(context: ToolAdminWebContext) -> WebModule:
    def register_callbacks(app: object, _services: object) -> None:
        register_tool_admin_callbacks(app, context)

    return WebModule(
        name='ada-tool-configuration',
        asset_layers=(
            AssetLayer(
                name='ada_tool_configuration',
                load_order=710,
                package='ada.configuration.tools',
            ),
        ),
        register_callbacks=register_callbacks,
    )
