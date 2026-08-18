# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Inyecta IDs y servicios para conectar Tools con el Manager genérico.
from collections.abc import Callable
from dataclasses import dataclass

from ada.configuration.tools.services import ToolConfigurationServices


@dataclass(frozen=True, slots=True)
class ToolAdminWebContext:
    services: ToolConfigurationServices
    draft_store_id: object
    draft_save_action_id: object
    workflow_refresh_signal_id: object
    draft_owner_provider: Callable[[], str]
    can_manage: Callable[[], bool] = lambda: True
    source_name: str = 'Source'
    projection_name: str = 'Projection'
