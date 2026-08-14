# Espejo pedagógico del API público de ada.ui.features.alarms.
# Expone exactamente los contratos productivos, sin aliases ni comportamiento adicional.
from .dashboard import (
    AlarmBaselineDefinition,
    AlarmBaselineLayout,
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
    AlarmDashboardRouteDefinition,
    AlarmPresentationInteraction,
    AlarmRouteTone,
    AlarmVisibilityStrategy,
    alarm_card_identity_attributes,
    alarm_card_presentation_attributes,
    alarm_geometry_scope_attributes,
    alarm_presentation_scope_attributes,
    alarm_queue_lane_attributes,
    alarm_visibility_scope_attributes,
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
    'AlarmPresentationInteraction',
    'AlarmRouteTone',
    'AlarmVisibilityStrategy',
    'alarm_card_identity_attributes',
    'alarm_card_presentation_attributes',
    'alarm_geometry_scope_attributes',
    'alarm_presentation_scope_attributes',
    'alarm_queue_lane_attributes',
    'alarm_visibility_scope_attributes',
    'build_alarm_dashboard_baseline',
    'build_alarm_dashboard_route_layer',
    'build_integrated_operations_alarm_baseline',
    'build_process_alarm_baseline',
    'create_ada_alarms_module',
]
