from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest
from ada.features.alarms.core.errors import AlarmDefinitionError
from ada.features.alarms.core.management_summary.models import (
    AlarmManagementSummarySegmentState,
    AlarmManagementSummaryState,
)


def create_alarm_management_summary_state(
    *,
    manifest: ToolManifest,
    segments: tuple[AlarmManagementSummarySegmentState, ...],
) -> AlarmManagementSummaryState:
    state = AlarmManagementSummaryState(segments=segments)
    for segment in state.segments:
        section = manifest.section(segment.section_key)
        if section.scope is not segment.scope:
            raise AlarmDefinitionError(
                f'Alarm management summary section {segment.section_key!r} scope does not match '
                'the tool manifest'
            )
        path_keys = tuple(item.key for item in manifest.path(segment.section_key))
        if 'alarm_management' not in path_keys:
            raise AlarmDefinitionError(
                f'Alarm management summary section {segment.section_key!r} must belong to '
                "'alarm_management'"
            )
    return state
