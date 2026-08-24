# La configuración proyectada es opcional: ante ausencia o incompatibilidad se conserva el baseline operativo.
from __future__ import annotations

from dataclasses import dataclass

from ada.contracts.tool_manifest import ToolManifest, ToolManifestResolution

from .errors import AdaSurfaceError
from .models import AdaSurfaceComposition
from .registry import AdaSurfaceRegistry


@dataclass(frozen=True, slots=True)
class AdaSurfaceResolution:
    configuration: ToolManifestResolution
    surface: AdaSurfaceComposition


def resolve_ada_surface(
    *,
    baseline_manifest: ToolManifest,
    configuration: ToolManifestResolution,
    registry: AdaSurfaceRegistry,
) -> AdaSurfaceResolution:
    baseline = registry.compose(baseline_manifest)
    if not configuration.ready:
        return AdaSurfaceResolution(configuration=configuration, surface=baseline)
    try:
        configured = registry.compose(configuration.require_manifest())
    except AdaSurfaceError:
        return AdaSurfaceResolution(
            configuration=ToolManifestResolution.invalid(),
            surface=baseline,
        )
    return AdaSurfaceResolution(configuration=configuration, surface=configured)
