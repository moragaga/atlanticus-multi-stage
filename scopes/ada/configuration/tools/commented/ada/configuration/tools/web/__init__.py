# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Configuración de herramientas del scope ADA. Convierte datos administrativos mínimos en contratos runtime ToolManifest sin acoplar el dominio a la UI.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from ada.configuration.tools.web.layout import build_tool_admin_configuration
from ada.configuration.tools.web.models import ToolAdminWebContext
from ada.configuration.tools.web.module import create_tool_admin_web_module

__all__ = [
    'ToolAdminWebContext',
    'build_tool_admin_configuration',
    'create_tool_admin_web_module',
]
