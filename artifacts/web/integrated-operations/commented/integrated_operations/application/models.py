from __future__ import annotations

from dataclasses import dataclass

# La composición principal distingue la surface operacional del Manager administrativo.
from ada.compositions.manager_surface import AdaManagerSurfaceComposition
from ada.compositions.surface import AdaSurfaceComposition
from ada.contracts.tool_manifest import ToolManifestResolution


@dataclass(frozen=True, slots=True)
class IntegratedOperationsApplicationComposition:
    configuration_resolution: ToolManifestResolution
    operational: AdaSurfaceComposition
    manager: AdaManagerSurfaceComposition | None = None
