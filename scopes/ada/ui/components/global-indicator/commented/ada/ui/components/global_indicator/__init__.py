# Espejo comentado: expone la API pública canónica del componente global indicator.
# La lógica ejecutable es idéntica al archivo productivo.
from .build import build_global_indicator, build_global_indicators
from .definitions import GlobalIndicatorDefinition, GlobalIndicatorMeasurementDefinition
from .errors import GlobalIndicatorDefinitionError
from .mappers import (
    map_global_indicator_collection,
    map_global_indicator_measurement,
    map_global_indicator_state,
)
from .models import (
    GlobalIndicatorCollection,
    GlobalIndicatorMeasurementKind,
    GlobalIndicatorMeasurementState,
    GlobalIndicatorState,
    GlobalIndicatorStyle,
)
from .module import ADA_GLOBAL_INDICATOR_ASSET_LAYER, create_ada_global_indicator_module

__all__ = [
    'ADA_GLOBAL_INDICATOR_ASSET_LAYER',
    'GlobalIndicatorCollection',
    'GlobalIndicatorDefinition',
    'GlobalIndicatorDefinitionError',
    'GlobalIndicatorMeasurementDefinition',
    'GlobalIndicatorMeasurementKind',
    'GlobalIndicatorMeasurementState',
    'GlobalIndicatorState',
    'GlobalIndicatorStyle',
    'build_global_indicator',
    'build_global_indicators',
    'create_ada_global_indicator_module',
    'map_global_indicator_collection',
    'map_global_indicator_measurement',
    'map_global_indicator_state',
]
