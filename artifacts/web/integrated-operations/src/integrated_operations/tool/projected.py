from __future__ import annotations

from typing import Protocol

from ada.configuration.tools.errors import ToolConfigurationProjectionError
from ada.configuration.tools.projection import ToolConfigurationProjection
from ada.contracts.tool_manifest import ToolManifestLookupError, ToolManifestResolution

_TOOL_KEY = 'integrated_operations'


class ToolProjectionReader(Protocol):
    def load(self) -> ToolConfigurationProjection | None: ...


def resolve_projected_integrated_operations_manifest(
    repository: ToolProjectionReader,
) -> ToolManifestResolution:
    try:
        projection = repository.load()
    except ToolConfigurationProjectionError:
        return ToolManifestResolution.source_error()
    if projection is None:
        return ToolManifestResolution.not_projected()
    try:
        manifest = projection.registry.require(_TOOL_KEY)
    except ToolManifestLookupError:
        return ToolManifestResolution.invalid()
    return ToolManifestResolution.resolved(manifest)
