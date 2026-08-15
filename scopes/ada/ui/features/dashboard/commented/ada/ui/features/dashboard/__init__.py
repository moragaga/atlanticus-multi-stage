# Superficie pública de los contratos puros de Dashboard antes de incorporar callbacks Dash.

from .definition import DashboardComponentDefinition, DashboardDefinition
from .errors import DashboardDefinitionError, TimeAxisError
from .models import (
    ComponentBundle,
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardToolConfiguration,
    TimeAxis,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    TimeSeriesWindow,
    build_component_bundle,
)
from .time_axis import TimeAxisBuilder

__all__ = [
    'ComponentBundle',
    'ComponentProjectionDefinition',
    'ComponentRendererDefinition',
    'ComponentRendererRegistry',
    'DashboardComponentDefinition',
    'DashboardDefinition',
    'DashboardDefinitionError',
    'DashboardToolConfiguration',
    'TimeAxis',
    'TimeAxisBuilder',
    'TimeAxisError',
    'TimeSeriesProjectionDefinition',
    'TimeSeriesSettings',
    'TimeSeriesWindow',
    'build_component_bundle',
]
