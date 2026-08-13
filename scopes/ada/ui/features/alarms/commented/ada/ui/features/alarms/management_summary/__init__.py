# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from .models import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryState,
    AlarmManagementSummaryTone,
)
from .presentation import build_alarm_management_summary
from .state import create_alarm_management_summary_state

__all__ = [
    'AlarmManagementSummarySegmentState',
    'AlarmManagementSummaryState',
    'AlarmManagementSummaryTone',
    'build_alarm_management_summary',
    'create_alarm_management_summary_state',
]
