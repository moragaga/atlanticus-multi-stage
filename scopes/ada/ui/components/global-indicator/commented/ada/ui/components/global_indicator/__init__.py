# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from .build import build_global_indicator, build_global_indicators
from .definitions import (
    GlobalIndicatorDefinition,
    IndicatorDefinition,
    IndicatorPropertiesDefinition,
)
from .errors import GlobalIndicatorDefinitionError
from .mappers import (
    map_global_indicator_data,
    map_global_indicators_data,
    map_indicator_data,
)
from .models import (
    GlobalIndicatorData,
    GlobalIndicatorsData,
    IndicatorData,
    IndicatorPropertiesData,
)
from .module import ADA_GLOBAL_INDICATOR_ASSET_LAYER, create_ada_global_indicator_module

__all__ = [
    'ADA_GLOBAL_INDICATOR_ASSET_LAYER',
    'GlobalIndicatorData',
    'GlobalIndicatorDefinition',
    'GlobalIndicatorDefinitionError',
    'GlobalIndicatorsData',
    'IndicatorData',
    'IndicatorDefinition',
    'IndicatorPropertiesData',
    'IndicatorPropertiesDefinition',
    'build_global_indicator',
    'build_global_indicators',
    'create_ada_global_indicator_module',
    'map_global_indicator_data',
    'map_global_indicators_data',
    'map_indicator_data',
]
