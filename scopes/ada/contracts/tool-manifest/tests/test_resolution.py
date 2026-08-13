import pytest

from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifestError,
    ToolManifestLookupError,
    ToolManifestResolution,
    ToolManifestResolutionStatus,
)


def test_ready_resolution_requires_and_returns_manifest() -> None:
    resolution = ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST)

    assert resolution.ready
    assert resolution.status is ToolManifestResolutionStatus.READY
    assert resolution.require_manifest() is INTEGRATED_OPERATIONS_MANIFEST


def test_unavailable_resolution_never_exposes_partial_manifest() -> None:
    resolution = ToolManifestResolution.not_projected()

    assert not resolution.ready
    assert resolution.manifest is None
    with pytest.raises(ToolManifestLookupError, match='not_projected'):
        resolution.require_manifest()


def test_resolution_rejects_invalid_state_combinations() -> None:
    with pytest.raises(ToolManifestError, match='requires a manifest'):
        ToolManifestResolution(ToolManifestResolutionStatus.READY)

    with pytest.raises(ToolManifestError, match='cannot include a manifest'):
        ToolManifestResolution(
            ToolManifestResolutionStatus.INVALID,
            INTEGRATED_OPERATIONS_MANIFEST,
        )
