# Declara el contexto Web de Tools e inyecta el store donde el editor informa su revisión actual al host.
# El módulo conserva su lógica propia mientras Manager decide el lifecycle a partir de esa señal.

from collections.abc import Callable
from dataclasses import dataclass

from ada.configuration.tools.services import ToolConfigurationServices


@dataclass(frozen=True, slots=True)
class ToolAdminWebContext:
    services: ToolConfigurationServices
    draft_store_id: object
    draft_save_action_id: object
    workflow_refresh_signal_id: object
    editor_revision_store_id: object
    draft_owner_provider: Callable[[], str]
    can_manage: Callable[[], bool] = lambda: True
    source_name: str = 'Source'
    projection_name: str = 'Projection'
