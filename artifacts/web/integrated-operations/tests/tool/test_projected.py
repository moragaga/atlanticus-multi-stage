from types import SimpleNamespace

from ada.configuration.tools.errors import ToolConfigurationProjectionError
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifestResolutionStatus,
)
from integrated_operations.tool.projected import resolve_projected_integrated_operations_manifest


class ProjectionReader:
    def __init__(self, projection=None, error: Exception | None = None) -> None:
        self._projection = projection
        self._error = error

    def load(self):
        if self._error is not None:
            raise self._error
        return self._projection


def test_projected_manifest_resolves_the_only_projected_tool() -> None:
    resolution = resolve_projected_integrated_operations_manifest(
        ProjectionReader(SimpleNamespace(manifest=INTEGRATED_OPERATIONS_MANIFEST))
    )

    assert resolution.status is ToolManifestResolutionStatus.READY
    assert resolution.require_manifest() == INTEGRATED_OPERATIONS_MANIFEST


def test_projected_manifest_reports_not_projected_when_projection_is_absent() -> None:
    resolution = resolve_projected_integrated_operations_manifest(ProjectionReader())

    assert resolution.status is ToolManifestResolutionStatus.NOT_PROJECTED


def test_projected_manifest_reports_source_error_when_projection_cannot_be_loaded() -> None:
    resolution = resolve_projected_integrated_operations_manifest(
        ProjectionReader(error=ToolConfigurationProjectionError('projection unavailable'))
    )

    assert resolution.status is ToolManifestResolutionStatus.SOURCE_ERROR
