# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from .errors import AlarmDefinitionError
from .module import ADA_ALARMS_ASSET_LAYER, create_ada_alarms_module

__all__ = [
    'ADA_ALARMS_ASSET_LAYER',
    'AlarmDefinitionError',
    'create_ada_alarms_module',
]
