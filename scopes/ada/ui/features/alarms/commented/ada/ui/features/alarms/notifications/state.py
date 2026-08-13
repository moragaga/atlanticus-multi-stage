# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope

from ..errors import AlarmDefinitionError
from .models import AlarmStatusState


# Alarm Status pertenece a Notifications y valida su sección global antes de crear estado.
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
