from types import SimpleNamespace

import integrated_operations.application.composition as composition


def test_web_definition_mounts_dashboard_at_application_root(monkeypatch, tmp_path) -> None:
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
        flask_config={'SECRET_KEY': 'secret'},
    )

    assert definition.metadata is metadata
    assert definition.modules == ('identity', 'users', 'io-module')
    assert definition.page_packages == ('integrated_operations.pages',)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'secret'}
    assert definition.asset_layers == (composition.APPLICATION_ASSET_LAYER,)


def test_application_asset_layer_is_local_and_filename_ordered() -> None:
    layer = composition.APPLICATION_ASSET_LAYER

    assert layer.package is None
    assert layer.source_directory is not None
    assert layer.filename_ordered is True
    assert layer.load_order == 900
