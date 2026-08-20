from email import message_from_bytes
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
WHEELS = ROOT / 'wheels'
EXPECTED_INTERNAL_PACKAGES = {
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
    'atlanticus-web-navigation',
    'atlanticus-web-navigation-configuration',
    'atlanticus-web-observability',
    'atlanticus-web-users',
    'atlanticus-web-users-activity',
    'atlanticus-web-users-configuration',
    'atlanticus-web-users-cosmos',
}


def test_internal_wheel_closure_is_present() -> None:
    metadata = [_wheel_metadata(path) for path in WHEELS.glob('*.whl')]
    names = {item['Name'].lower().replace('_', '-') for item in metadata}

    assert names == EXPECTED_INTERNAL_PACKAGES


def test_internal_wheels_target_python_3142() -> None:
    for wheel in WHEELS.glob('*.whl'):
        metadata = _wheel_metadata(wheel)
        assert metadata['Requires-Python'] == '==3.14.2'


def _wheel_metadata(path: Path):
    with ZipFile(path) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith('.dist-info/METADATA')
        )
        return message_from_bytes(archive.read(metadata_name))
