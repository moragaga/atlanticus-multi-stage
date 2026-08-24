from dataclasses import dataclass

from dash import html

from ada.compositions.surface import AdaSurfaceComposition, AdaSurfaceRegistry, resolve_ada_surface
from ada.contracts.tool_manifest import (
    ToolManifest,
    ToolManifestResolution,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
)
from atlanticus.web.services import ServiceRegistry


@dataclass(frozen=True, slots=True)
class FakeAdapter:
    key: str
    supported_tool_key: str

    def supports(self, manifest: ToolManifest) -> bool:
        return manifest.tool_key == self.supported_tool_key

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
        return AdaSurfaceComposition(
            adapter_key=self.key,
            manifest=manifest,
            modules=(),
            builder=lambda _services: html.Div(manifest.display_name),
        )


def test_absent_configuration_keeps_baseline_surface() -> None:
    baseline = _manifest('integrated_operations')
    registry = AdaSurfaceRegistry((FakeAdapter('integrated_operations', baseline.tool_key),))

    resolution = resolve_ada_surface(
        baseline_manifest=baseline,
        configuration=ToolManifestResolution.not_projected(),
        registry=registry,
    )

    assert resolution.configuration == ToolManifestResolution.not_projected()
    assert resolution.surface.manifest == baseline


def test_valid_configuration_can_select_another_registered_surface_type() -> None:
    baseline = _manifest('integrated_operations')
    process = _manifest('flotation_process')
    registry = AdaSurfaceRegistry(
        (
            FakeAdapter('integrated_operations', baseline.tool_key),
            FakeAdapter('process', process.tool_key),
        )
    )

    resolution = resolve_ada_surface(
        baseline_manifest=baseline,
        configuration=ToolManifestResolution.resolved(process),
        registry=registry,
    )

    assert resolution.configuration.ready is True
    assert resolution.surface.adapter_key == 'process'
    assert resolution.surface.manifest == process


def test_unsupported_projected_configuration_falls_back_to_baseline_and_becomes_invalid() -> None:
    baseline = _manifest('integrated_operations')
    unsupported = _manifest('unknown_tool')
    registry = AdaSurfaceRegistry((FakeAdapter('integrated_operations', baseline.tool_key),))

    resolution = resolve_ada_surface(
        baseline_manifest=baseline,
        configuration=ToolManifestResolution.resolved(unsupported),
        registry=registry,
    )

    assert resolution.configuration == ToolManifestResolution.invalid()
    assert resolution.surface.manifest == baseline


def test_source_error_keeps_baseline_and_diagnostic_status() -> None:
    baseline = _manifest('integrated_operations')
    registry = AdaSurfaceRegistry((FakeAdapter('integrated_operations', baseline.tool_key),))

    resolution = resolve_ada_surface(
        baseline_manifest=baseline,
        configuration=ToolManifestResolution.source_error(),
        registry=registry,
    )

    assert resolution.configuration == ToolManifestResolution.source_error()
    assert resolution.surface.manifest == baseline
    assert resolution.surface.build(ServiceRegistry()).to_plotly_json()['props']['children'] == (
        baseline.display_name
    )


def _manifest(tool_key: str) -> ToolManifest:
    return ToolManifest(
        tool_key=tool_key,
        display_name=tool_key.replace('_', ' ').title(),
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        sections=(
            ToolSection(
                key='body',
                display_name='Body',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.GLOBAL,
            ),
        ),
    )
