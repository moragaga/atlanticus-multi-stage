# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Capability genérica del Configuration Manager de Atlanticus. Mantiene contratos y UI administrativa sin conocer dominios ni persistencias concretas.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

from atlanticus.web.manager.web.assets import (
    ATLANTICUS_MANAGER_LAYER_NAME,
    manager_asset_layer,
)
from atlanticus.web.manager.web.callbacks import register_manager_callbacks
from atlanticus.web.manager.web.ids import workflow_projection_signal_id
from atlanticus.web.manager.web.layout import build_manager_shell

__all__ = [
    'ATLANTICUS_MANAGER_LAYER_NAME',
    'build_manager_shell',
    'manager_asset_layer',
    'register_manager_callbacks',
    'workflow_projection_signal_id',
]
