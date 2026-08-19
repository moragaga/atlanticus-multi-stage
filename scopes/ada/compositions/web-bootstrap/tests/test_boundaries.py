from pathlib import Path


def test_productive_source_does_not_read_environment_or_provision_on_import() -> None:
    source_root = Path(__file__).parents[1] / 'src'
    content = '\n'.join(path.read_text() for path in source_root.rglob('*.py'))

    assert 'os.environ' not in content
    assert 'os.getenv' not in content
    assert 'ensure_database(' not in content
    assert 'ensure_containers(' not in content
    assert 'ATLANTICUS_COSMOS_' not in content


def test_r17a_composition_is_not_modified_by_bootstrap_package() -> None:
    bootstrap_source = Path(__file__).parents[1] / 'src'
    content = '\n'.join(path.read_text() for path in bootstrap_source.rglob('*.py'))

    assert 'create_ada_application_modules' in content
    assert 'create_web_application' not in content
    assert 'CosmosProvisioner' not in content


def test_runtime_bootstrap_does_not_trigger_configuration_synchronization_or_sharepoint() -> None:
    bootstrap_source = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'compositions'
        / 'web_bootstrap'
        / 'bootstrap.py'
    ).read_text()
    runtime_function = bootstrap_source.split('def create_ada_configuration_backends', 1)[0]

    assert 'synchronize_ada_access_projections' not in runtime_function
    assert '.sharepoint()' not in runtime_function
    assert 'sharepoint_paths' not in runtime_function
