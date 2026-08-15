# Superficie pública de la feature Dashboard.
from .callbacks import register_dashboard_callbacks
from .definition import DashboardComponentDefinition, DashboardDefinition
from .distribution import distribute_shared_snapshot
from .errors import DashboardDefinitionError, DashboardStoreError, TimeAxisError
from .ids import DashboardComponentIds, DashboardPollingIds
from .models import (
    ComponentBundle,
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    TimeAxis,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    TimeSeriesWindow,
    build_component_bundle,
)
from .module import create_ada_dashboard_module
from .mount import DashboardMount, build_dashboard_mount
from .polling import (
    DashboardChannelUpdate,
    DashboardPollingErrorHandler,
    dashboard_snapshot_channels,
    read_dashboard_channel_update,
    register_dashboard_polling_callbacks,
)
from .serialization import (
    decode_component_data_snapshot,
    decode_component_state_snapshot,
    decode_component_time_series_snapshot,
    encode_component_data_snapshot,
    encode_component_state_snapshot,
    encode_component_time_series_snapshot,
)
from .time_axis import TimeAxisBuilder
from .wiring import (
    ComponentRenderResult,
    ComponentRenderState,
    ComponentRenderStatus,
    encode_render_status,
    initial_render_status,
    render_component_from_stores,
    resolve_component_cover,
)

__all__ = [
    'ComponentBundle',
    'ComponentProjectionDefinition',
    'ComponentRenderResult',
    'ComponentRendererDefinition',
    'ComponentRendererRegistry',
    'ComponentRenderState',
    'ComponentRenderStatus',
    'DashboardComponentDefinition',
    'DashboardComponentIds',
    'DashboardDefinition',
    'DashboardDefinitionError',
    'DashboardMount',
    'DashboardChannelUpdate',
    'DashboardPollingErrorHandler',
    'DashboardPollingIds',
    'DashboardPollingSettings',
    'DashboardStoreError',
    'DashboardToolConfiguration',
    'TimeAxis',
    'TimeAxisBuilder',
    'TimeAxisError',
    'TimeSeriesProjectionDefinition',
    'TimeSeriesSettings',
    'TimeSeriesWindow',
    'build_component_bundle',
    'build_dashboard_mount',
    'create_ada_dashboard_module',
    'dashboard_snapshot_channels',
    'decode_component_data_snapshot',
    'decode_component_state_snapshot',
    'decode_component_time_series_snapshot',
    'encode_component_data_snapshot',
    'encode_component_state_snapshot',
    'encode_component_time_series_snapshot',
    'distribute_shared_snapshot',
    'encode_render_status',
    'initial_render_status',
    'read_dashboard_channel_update',
    'register_dashboard_callbacks',
    'register_dashboard_polling_callbacks',
    'render_component_from_stores',
    'resolve_component_cover',
]
