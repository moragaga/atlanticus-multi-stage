# Espejo pedagógico del API del dashboard de alarmas.
# Mantiene separadas baseline, rutas, reproducción y scheduling.
from .baseline import (
    AlarmBaselineDefinition,
    AlarmBaselineLayout,
    AlarmBaselineTarget,
    AlarmBaselineTargetKind,
)
from .geometry import alarm_geometry_scope_attributes
from .playback import AlarmPresentationInteraction, alarm_presentation_scope_attributes
from .presentation import (
    build_alarm_dashboard_baseline,
    build_alarm_dashboard_route_layer,
    build_integrated_operations_alarm_baseline,
    build_process_alarm_baseline,
)
from .routes import (
    AlarmDashboardRouteDefinition,
    AlarmRouteTone,
    alarm_card_identity_attributes,
    alarm_card_presentation_attributes,
)
from .scheduling import (
    AlarmVisibilityStrategy,
    alarm_queue_lane_attributes,
    alarm_visibility_scope_attributes,
)

__all__ = [
    'AlarmBaselineDefinition',
    'AlarmBaselineLayout',
    'AlarmBaselineTarget',
    'AlarmBaselineTargetKind',
    'AlarmDashboardRouteDefinition',
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
]
