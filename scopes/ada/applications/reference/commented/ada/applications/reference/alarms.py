# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.ui.components.state_wrapper import ComponentCover
from ada.features.alarms.management_summary import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryTone,
    build_alarm_management_summary,
    create_alarm_management_summary_state,
)
from ada.features.alarms.notifications import build_alarm_status


# La application composition arma el mock actual de gestión sin devolver ownership al Header.
def build_reference_alarm_management_summary(manifest: ToolManifest):
    state = create_alarm_management_summary_state(
        manifest=manifest,
        segments=(
            AlarmManagementSummarySegmentState(
                section_key=_alarm_management_section_key(manifest, ToolScope.MINE),
                scope=ToolScope.MINE,
                group='G3',
                management_percentage=60,
                tone=AlarmManagementSummaryTone.ATTENTION,
            ),
            AlarmManagementSummarySegmentState(
                section_key=_alarm_management_section_key(manifest, ToolScope.PLANT),
                scope=ToolScope.PLANT,
                group='G1',
                management_percentage=45,
                tone=AlarmManagementSummaryTone.CRITICAL,
            ),
        ),
    )
    return build_alarm_management_summary(state, cover=ComponentCover.stale())


# Resuelve la key derivada sin reproducir fuera del contrato su algoritmo de composición.
def _alarm_management_section_key(manifest: ToolManifest, scope: ToolScope) -> str:
    subcomponent = {
        ToolScope.MINE: 'mine',
        ToolScope.PLANT: 'plant',
    }[scope]
    return manifest.subcomponent(
        component='alarm_management',
        subcomponent=subcomponent,
    ).key


# Alarm Status conserva el estado En construcción de la referencia actual.
def build_reference_alarm_status():
    return build_alarm_status(None, cover=ComponentCover.construction())
