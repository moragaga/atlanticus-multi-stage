# Espejo comentado de la implementación productiva.
# Mantiene exactamente el mismo contrato y comportamiento del archivo en src/.
from .errors import StateWrapperDefinitionError
from .models import ComponentAvailability, DataFreshness, StateWrapperState
from .module import ADA_STATE_WRAPPER_ASSET_LAYER, create_ada_state_wrapper_module
from .presentation import build_state_wrapper

__all__ = [
    'ADA_STATE_WRAPPER_ASSET_LAYER',
    'ComponentAvailability',
    'DataFreshness',
    'StateWrapperDefinitionError',
    'StateWrapperState',
    'build_state_wrapper',
    'create_ada_state_wrapper_module',
]
