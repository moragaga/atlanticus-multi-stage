from dataclasses import dataclass, replace
from types import SimpleNamespace

from dash import html

import integrated_operations.application.composition as composition
from ada.compositions.surface import AdaSurfaceComposition, AdaSurfaceRegistry
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolManifest,
    ToolManifestResolution,
)


@dataclass(frozen=True, slots=True)
class FakeSurfaceAdapter:
    key: str
    supported_tool_key: str

    def supports(self, manifest: ToolManifest) -> bool:
        return manifest.tool_key == self.supported_tool_key

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
        return AdaSurfaceComposition(
            adapter_key=self.key,
            manifest=manifest,
            modules=(f'{self.key}-module',),
            builder=lambda _services: html.Div(manifest.display_name),
        )


def test_application_composition_keeps_projected_operational_manifest() -> None:
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST)
    )

    assert application.operational_resolution.configuration.ready is True
    assert application.operational.adapter_key == 'integrated_operations'
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST
    assert application.manager is None
    assert application.administration_route_prefix == composition.MANAGER_ROUTE_PREFIX


def test_application_composition_keeps_baseline_when_projection_is_absent() -> None:
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.not_projected()
    )

    assert (
        application.operational_resolution.configuration == ToolManifestResolution.not_projected()
    )
    assert application.operational.adapter_key == 'integrated_operations'
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_registered_surface_adapter_can_replace_baseline_from_valid_configuration() -> None:
    alternate_manifest = replace(INTEGRATED_OPERATIONS_MANIFEST, tool_key='alternate_reference')
    registry = AdaSurfaceRegistry(
        (
            FakeSurfaceAdapter('integrated_operations', 'integrated_operations'),
            FakeSurfaceAdapter('alternate', 'alternate_reference'),
        )
    )

    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.resolved(alternate_manifest),
        surface_registry=registry,
    )

    assert application.operational_resolution.configuration.ready is True
    assert application.operational.adapter_key == 'alternate'
    assert application.operational.manifest == alternate_manifest


def test_web_definition_delegates_generic_host_with_concrete_artifact_inputs(monkeypatch) -> None:
    metadata = SimpleNamespace()
    application = SimpleNamespace()
    captured = {}
    expected = object()

    def build_generic(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(composition, 'build_ada_web_definition', build_generic)

    result = composition.build_web_definition(
        metadata=metadata,
        deployment_modules=('identity', 'users'),
        composition=application,
        flask_config={'SECRET_KEY': 'secret'},
    )

    assert result is expected
    assert captured == {
        'import_name': 'integrated_operations',
        'metadata': metadata,
        'deployment_modules': ('identity', 'users'),
        'composition': application,
        'page_packages': ('integrated_operations.pages',),
        'asset_layers': (composition.APPLICATION_ASSET_LAYER,),
        'flask_config': {'SECRET_KEY': 'secret'},
    }


def test_incompatible_projected_manifest_falls_back_to_baseline_and_stays_invalid() -> None:
    invalid_manifest = replace(INTEGRATED_OPERATIONS_MANIFEST, tool_key='other_tool')

    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.resolved(invalid_manifest)
    )

    assert application.operational_resolution.configuration == ToolManifestResolution.invalid()
    assert application.operational.adapter_key == 'integrated_operations'
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_source_error_keeps_baseline_operational() -> None:
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.source_error()
    )

    assert application.operational_resolution.configuration == ToolManifestResolution.source_error()
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_application_asset_layer_is_concrete_and_filename_ordered() -> None:
    layer = composition.APPLICATION_ASSET_LAYER

    assert layer.package is None
    assert layer.source_directory is not None
    assert layer.filename_ordered is True
    assert layer.load_order == 900
