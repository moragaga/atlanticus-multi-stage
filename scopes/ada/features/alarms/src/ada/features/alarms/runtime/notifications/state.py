from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope
from ada.features.alarms.core.errors import AlarmDefinitionError
from ada.features.alarms.core.notifications.models import AlarmStatusState


def create_alarm_status_state(
    *,
    manifest: ToolManifest,
    active_count: int,
    managed_count: int,
) -> AlarmStatusState:
    header = manifest.section('header')
    section = manifest.section('alarm_status')
    if section.parent_key != header.key or section.scope is not ToolScope.GLOBAL:
        raise AlarmDefinitionError(
            "Tool manifest alarm_status must be global and belong to 'header'"
        )
    return AlarmStatusState(active_count=active_count, managed_count=managed_count)
