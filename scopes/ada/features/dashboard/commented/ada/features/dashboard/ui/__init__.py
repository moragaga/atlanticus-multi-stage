# Espejo pedagógico en español; la lógica ejecutable es equivalente al archivo productivo.
from .callbacks import register_dashboard_callbacks
from .ids import DashboardComponentIds, DashboardPollingIds
from .module import create_ada_dashboard_module
from .mount import DashboardMount, build_dashboard_mount
from .polling import (
    DashboardChannelUpdate,
    DashboardPollingErrorHandler,
    dashboard_snapshot_channels,
    read_dashboard_channel_update,
    register_dashboard_polling_callbacks,
)
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
    'ComponentRenderResult',
    'ComponentRenderState',
    'ComponentRenderStatus',
    'DashboardChannelUpdate',
    'DashboardComponentIds',
    'DashboardMount',
    'DashboardPollingErrorHandler',
    'DashboardPollingIds',
    'build_dashboard_mount',
    'create_ada_dashboard_module',
    'dashboard_snapshot_channels',
    'encode_render_status',
    'initial_render_status',
    'read_dashboard_channel_update',
    'register_dashboard_callbacks',
    'register_dashboard_polling_callbacks',
    'render_component_from_stores',
    'resolve_component_cover',
]
