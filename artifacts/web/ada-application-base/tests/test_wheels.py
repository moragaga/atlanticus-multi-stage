import tomllib
from email import message_from_bytes
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
WHEELS = ROOT / 'wheels'
EXPECTED_INTERNAL_PACKAGES = {
    'ada-composition-configuration-manager',
    'ada-composition-web-application',
    'ada-composition-web-bootstrap',
    'ada-composition-web-deployment',
    'ada-configuration-tools',
    'ada-contracts-tool-manifest',
    'atlanticus-cosmos',
    'atlanticus-http',
    'atlanticus-kernel',
    'atlanticus-observability',
    'atlanticus-web',
    'atlanticus-web-composition-navigation-activity',
    'atlanticus-web-composition-runtime-infrastructure',
    'atlanticus-web-composition-sharepoint-http',
    'atlanticus-web-composition-users-navigation',
    'atlanticus-web-identity',
    'atlanticus-web-identity-app-service',
    'atlanticus-web-identity-local',
    'atlanticus-web-manager',
    'atlanticus-web-navigation',
    'atlanticus-web-navigation-configuration',
    'atlanticus-web-observability',
    'atlanticus-web-users',
    'atlanticus-web-users-activity',
    'atlanticus-web-users-configuration',
    'atlanticus-web-users-cosmos',
    'atlanticus-web-users-local',
}

CRITICAL_PATH_PINNED_WHEELS = {
    'ada-composition-configuration-manager': (
        '0.1.15',
        'ada_composition_configuration_manager-0.1.15-py3-none-any.whl',
    ),
    'ada-composition-web-bootstrap': (
        '0.1.6',
        'ada_composition_web_bootstrap-0.1.6-py3-none-any.whl',
    ),
    'ada-composition-web-deployment': (
        '0.1.8',
        'ada_composition_web_deployment-0.1.8-py3-none-any.whl',
    ),
    'atlanticus-web-manager': (
        '0.3.9',
        'atlanticus_web_manager-0.3.9-py3-none-any.whl',
    ),
    'atlanticus-web-identity': (
        '0.1.0',
        'atlanticus_web_identity-0.1.0-py3-none-any.whl',
    ),
    'atlanticus-web-identity-local': (
        '0.1.0',
        'atlanticus_web_identity_local-0.1.0-py3-none-any.whl',
    ),
    'atlanticus-web-users-configuration': (
        '0.1.5',
        'atlanticus_web_users_configuration-0.1.5-py3-none-any.whl',
    ),
    'atlanticus-web-users-cosmos': (
        '0.1.5',
        'atlanticus_web_users_cosmos-0.1.5-py3-none-any.whl',
    ),
    'atlanticus-web-users-local': (
        '0.1.0',
        'atlanticus_web_users_local-0.1.0-py3-none-any.whl',
    ),
}


def test_internal_wheel_closure_is_present() -> None:
    metadata = [_wheel_metadata(path) for path in WHEELS.glob('*.whl')]
    names = {item['Name'].lower().replace('_', '-') for item in metadata}

    assert names == EXPECTED_INTERNAL_PACKAGES
    assert len(metadata) == len(EXPECTED_INTERNAL_PACKAGES)


def test_internal_wheels_target_python_3142() -> None:
    for wheel in WHEELS.glob('*.whl'):
        metadata = _wheel_metadata(wheel)
        assert metadata['Requires-Python'] == '==3.14.2'


def test_critical_internal_wheels_are_path_pinned() -> None:
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = set(project['project']['dependencies'])
    sources = project['tool']['uv']['sources']
    lock = tomllib.loads((ROOT / 'uv.lock').read_text(encoding='utf-8'))
    locked_packages = {package['name']: package for package in lock['package']}

    for package, (version, filename) in CRITICAL_PATH_PINNED_WHEELS.items():
        assert f'{package}=={version}' in dependencies
        expected_source = {'path': f'wheels/{filename}'}
        assert sources[package] == expected_source
        assert locked_packages[package]['source'] == expected_source


def _wheel_metadata(path: Path):
    with ZipFile(path) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith('.dist-info/METADATA')
        )
        return message_from_bytes(archive.read(metadata_name))
