# Traduce configuración y snapshot runtime al estado que consume la presentación.
from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolSourceKey
from ada.runtime.web import RuntimeSnapshot

from .models import TimeStatusSourceState, TimeStatusState

_SOURCE_LABELS = {
    ToolSourceKey.PI: 'PI System',
    ToolSourceKey.DISPATCH: 'Dispatch',
}


def create_time_status_state(
    *,
    manifest: ToolManifest,
    snapshot: RuntimeSnapshot,
) -> TimeStatusState:
    return TimeStatusState(
        tool_key=manifest.tool_key,
        sources=tuple(
            TimeStatusSourceState(
                key=source.key,
                label=_SOURCE_LABELS[source.key],
                stale_after_seconds=source.stale_after_seconds,
                runtime_state=snapshot.source(source.key.value),
            )
            for source in manifest.sources
        ),
    )
