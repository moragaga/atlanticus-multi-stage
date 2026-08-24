# La superficie principal separa el estado de configuración del render operativo.
# Un manifiesto no proyectado, inválido o no legible nunca se sustituye silenciosamente por una definición compilada.
from __future__ import annotations

from ada.compositions.integrated_operations import IntegratedOperationsToolComposition
from ada.contracts.tool_manifest import ToolManifestResolution, ToolManifestResolutionStatus
from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper
from ada.ui.framework.core import build_ready_scope
from atlanticus.web.services import ServiceRegistry
from integrated_operations.tool import build_integrated_operations_tool


def build_application_layout(
    _services: ServiceRegistry,
    *,
    resolution: ToolManifestResolution,
    composition: IntegratedOperationsToolComposition | None,
):
    if composition is not None:
        return build_integrated_operations_tool(composition)
    return _build_configuration_fallback(resolution)


def _build_configuration_fallback(resolution: ToolManifestResolution):
    cover = {
        ToolManifestResolutionStatus.NOT_PROJECTED: ComponentCover.construction(
            message=(
                'Configuration not available. '
                'The projected configuration for this tool is not available yet.'
            )
        ),
        ToolManifestResolutionStatus.INVALID: ComponentCover.source_error(
            message='Configuration invalid. The projected configuration is not compatible.'
        ),
        ToolManifestResolutionStatus.SOURCE_ERROR: ComponentCover.source_error(
            message='Configuration unavailable. The projected configuration could not be loaded.'
        ),
    }[resolution.status]
    return build_ready_scope(
        content=build_state_wrapper(
            cover=cover,
            class_name='integrated-operations__configuration-state',
            ready_name='tool-configuration',
        ),
        required=('tool-configuration',),
    )
