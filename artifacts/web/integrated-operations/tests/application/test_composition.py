from dataclasses import replace
from types import SimpleNamespace

import integrated_operations.application.composition as composition
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolManifestResolution


def test_web_definition_mounts_projected_dashboard_at_application_root(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
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
    metadata = SimpleNamespace()

    definition = composition.build_web_definition(
        metadata=metadata,
        deployment_modules=('identity', 'users'),
        tool_manifest_resolution=ToolManifestResolution.resolved(INTEGRATED_OPERATIONS_MANIFEST),
        flask_config={'SECRET_KEY': 'secret'},
    )

    assert definition.metadata is metadata
    assert definition.modules == ('identity', 'users', 'io-module')
    assert definition.page_packages == ('integrated_operations.pages',)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'secret'}
    assert definition.asset_layers == (composition.APPLICATION_ASSET_LAYER,)


def test_web_definition_does_not_mount_dashboard_when_projection_is_absent(tmp_path) -> None:
    definition = composition.build_web_definition(
        metadata=SimpleNamespace(),
        deployment_modules=('identity', 'users'),
        tool_manifest_resolution=ToolManifestResolution.not_projected(),
    )

    assert definition.modules == ('identity', 'users')


def test_incompatible_projected_manifest_is_downgraded_to_invalid() -> None:
    invalid_manifest = replace(INTEGRATED_OPERATIONS_MANIFEST, tool_key='other_tool')

    resolution, tool_composition = composition._resolve_tool_composition(
        ToolManifestResolution.resolved(invalid_manifest)
    )

    assert resolution == ToolManifestResolution.invalid()
    assert tool_composition is None


def test_application_asset_layer_is_local_and_filename_ordered() -> None:
    layer = composition.APPLICATION_ASSET_LAYER

    assert layer.package is None
    assert layer.source_directory is not None
    assert layer.filename_ordered is True
    assert layer.load_order == 900
