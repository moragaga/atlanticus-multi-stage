from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifestResolution,
)


# Esta función es la frontera reemplazable por la proyección real de configuración.
def resolve_reference_tool_manifest() -> ToolManifestResolution:
    return ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST)
