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
    return build_integrated_operations_tool(composition)
