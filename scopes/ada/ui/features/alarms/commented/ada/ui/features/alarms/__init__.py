# Mantiene una fachada pública única para la feature transversal de alarmas.
from .dashboard import (
    AlarmBaselineDefinition,
    AlarmBaselineLayout,
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
    AlarmDashboardRouteDefinition,
    AlarmRouteTone,
    alarm_card_identity_attributes,
    alarm_geometry_scope_attributes,
    build_alarm_dashboard_baseline,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
    build_process_alarm_baseline,
)
from .errors import AlarmDefinitionError
from .module import ADA_ALARMS_ASSET_LAYER, create_ada_alarms_module

__all__ = [
    'ADA_ALARMS_ASSET_LAYER',
    'AlarmBaselineDefinition',
    'AlarmBaselineLayout',
    'AlarmBaselineTarget',
    'AlarmBaselineTargetKind',
    'AlarmDashboardRouteDefinition',
    'AlarmDefinitionError',
    'AlarmRouteTone',
    'alarm_card_identity_attributes',
    'alarm_geometry_scope_attributes',
    'build_alarm_dashboard_baseline',
    'build_alarm_dashboard_route_layer',
    'build_integrated_operations_alarm_baseline',
    'build_process_alarm_baseline',
    'create_ada_alarms_module',
]
