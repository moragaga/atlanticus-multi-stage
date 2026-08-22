# Expone el renderer semántico de historial de Tools como parte del contrato web del módulo.
# La composición puede registrar esta capacidad sin conocer detalles internos de la representación.

from ada.configuration.tools.web.layout import build_tool_admin_configuration
from ada.configuration.tools.web.models import ToolAdminWebContext
from ada.configuration.tools.web.module import create_tool_admin_web_module
from ada.configuration.tools.web.preview import build_tool_history_preview

__all__ = [
    'build_tool_history_preview',
    'ToolAdminWebContext',
    'build_tool_admin_configuration',
    'create_tool_admin_web_module',
]
