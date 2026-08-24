# El layout operativo siempre recibe una composición efectiva: proyectada cuando es válida o baseline en caso contrario.
from __future__ import annotations

from ada.compositions.integrated_operations import IntegratedOperationsToolComposition
from ada.contracts.tool_manifest import ToolManifestResolution
from atlanticus.web.services import ServiceRegistry
from integrated_operations.tool import build_integrated_operations_tool


def build_application_layout(
    _services: ServiceRegistry,
    *,
    configuration_resolution: ToolManifestResolution,
    composition: IntegratedOperationsToolComposition,
):
    # El estado real de configuración se conserva para la próxima composición visual sin bloquear el Body actual.
    # La ausencia de configuración nunca sustituye el Body por una pantalla de bloqueo.
    return build_integrated_operations_tool(composition)
