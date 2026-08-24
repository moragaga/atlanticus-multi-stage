from __future__ import annotations

from dataclasses import dataclass

from ada.compositions.surface import AdaSurfaceComposition
from ada.contracts.tool_manifest import ToolManifestResolution
from atlanticus.web.manager import ManagerSurface
from atlanticus.web.modules import WebModule


@dataclass(frozen=True, slots=True)
class ManagerSurfaceComposition:
    surface: ManagerSurface
    principal_binding: WebModule


@dataclass(frozen=True, slots=True)
class IntegratedOperationsApplicationComposition:
    configuration_resolution: ToolManifestResolution
    operational: AdaSurfaceComposition
    manager: ManagerSurfaceComposition | None = None
