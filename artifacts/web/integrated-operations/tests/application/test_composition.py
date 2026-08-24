from dataclasses import replace
from types import SimpleNamespace

import integrated_operations.application.composition as composition
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolManifestResolution
from integrated_operations.application.models import ManagerSurfaceComposition


def _patch_runtime_modules(monkeypatch) -> None:
    monkeypatch.setattr(
        composition,
        'SharedSnapshotReader',
        lambda repository, ttl_seconds: SimpleNamespace(
            repository=repository, ttl_seconds=ttl_seconds
        ),
    )
    monkeypatch.setattr(
        composition,
        'create_integrated_operations_tool_modules',
        lambda _composition, snapshot_reader: ('io-module',),
    )


def test_application_composition_keeps_projected_operational_manifest() -> None:
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST)
    )

    assert application.configuration_resolution.ready is True
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST
    assert application.manager is None


def test_application_composition_keeps_baseline_when_projection_is_absent() -> None:
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.not_projected()
    )

    assert application.configuration_resolution == ToolManifestResolution.not_projected()
    assert application.operational.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_web_definition_wires_operational_and_manager_modules(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_runtime_modules(monkeypatch)
    metadata = SimpleNamespace()
    manager_surface = SimpleNamespace(web_modules=('manager-services', 'manager-callbacks'))
    manager = ManagerSurfaceComposition(
        surface=manager_surface,
        principal_binding='manager-principal',
    )
    application = composition.build_application_composition(
        tool_manifest_resolution=ToolManifestResolution.not_projected(),
        manager=manager,
    )

    definition = composition.build_web_definition(
        metadata=metadata,
        deployment_modules=('identity', 'users'),
        composition=application,
        flask_config={'SECRET_KEY': 'secret'},
    )

    assert definition.metadata is metadata
    assert definition.modules == (
        'identity',
        'users',
        'io-module',
        'manager-principal',
        'manager-services',
        'manager-callbacks',
    )
    assert definition.page_packages == ('integrated_operations.pages',)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'secret'}
    assert definition.asset_layers == (composition.APPLICATION_ASSET_LAYER,)
    assert definition.layout.keywords['composition'] is application


def test_incompatible_projected_manifest_falls_back_to_baseline_and_stays_invalid() -> None:
    invalid_manifest = replace(INTEGRATED_OPERATIONS_MANIFEST, tool_key='other_tool')

    resolution, tool_composition = composition._resolve_tool_composition(
        ToolManifestResolution.resolved(invalid_manifest)
    )

    assert resolution == ToolManifestResolution.invalid()
    assert tool_composition.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_source_error_keeps_baseline_operational() -> None:
    resolution, tool_composition = composition._resolve_tool_composition(
        ToolManifestResolution.source_error()
    )

    assert resolution == ToolManifestResolution.source_error()
    assert tool_composition.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_application_asset_layer_is_local_and_filename_ordered() -> None:
    layer = composition.APPLICATION_ASSET_LAYER

    assert layer.package is None
    assert layer.source_directory is not None
    assert layer.filename_ordered is True
    assert layer.load_order == 900
