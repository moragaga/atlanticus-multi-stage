# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.ui.components.state_wrapper import ComponentCover
from ada.ui.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.ui.features.alarms.notifications import build_alarm_status


# La application composition arma el mock actual de gestión sin devolver ownership al Header.
def build_reference_alarm_management_summary(manifest: ToolManifest):
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key='alarm_management_mine',
                scope=ToolScope.MINE,
                group='G3',
                management_percentage=60,
                tone=AlarmManagementSummaryTone.ATTENTION,
            ),
            AlarmManagementSummarySegmentState(
                section_key='alarm_management_plant',
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=45,
                tone=AlarmManagementSummaryTone.CRITICAL,
            ),
        ),
    )
    return build_alarm_management_summary(state, cover=ComponentCover.stale())


# Alarm Status conserva el estado En construcción de la referencia actual.
def build_reference_alarm_status():
    return build_alarm_status(None, cover=ComponentCover.construction())
