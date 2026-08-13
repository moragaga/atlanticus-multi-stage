from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifestResolution,
)


def resolve_reference_tool_manifest() -> ToolManifestResolution:
    return ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST)
