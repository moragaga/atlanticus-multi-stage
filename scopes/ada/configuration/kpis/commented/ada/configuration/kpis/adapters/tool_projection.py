# Traduce Tool Projection estable a destinos COMPONENT que aceptan KPI.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

from ada.configuration.kpis.destinations import KpiDestination, KpiDestinationCatalog
from ada.configuration.tools.contracts import ToolProjectionRepository
from ada.contracts.tool_manifest import ToolSectionKind, ToolTarget


class ToolProjectionKpiDestinationProvider:
    def __init__(self, projection: ToolProjectionRepository) -> None:
        self._projection = projection

    def load(self) -> KpiDestinationCatalog | None:
        projection = self._projection.load()
        if projection is None:
            return None
        destinations = tuple(
            KpiDestination(key=section.key, display_name=section.display_name)
            for section in projection.manifest.sections_for_target(ToolTarget.KPI)
            if section.kind is ToolSectionKind.COMPONENT
        )
        return KpiDestinationCatalog(
            tool_projection_revision=projection.revision,
            destinations=destinations,
        )
