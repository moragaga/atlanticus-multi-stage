import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manager_surface_composition_is_reusable_and_not_operationally_coupled() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = set(document['project']['dependencies'])
    source = '\n'.join(path.read_text(encoding='utf-8') for path in (ROOT / 'src').rglob('*.py'))

    assert 'ada-ui-shell-header==0.2.0' in dependencies
    assert 'ada-ui-shell-navigation==0.1.0' in dependencies
    assert 'atlanticus-web-manager==0.3.12' in dependencies
    assert 'integrated_operations' not in source
    assert 'ada.compositions.surface' not in source
    assert 'ada.compositions.configuration_manager' not in source


def test_manager_surface_package_has_commented_python_mirror() -> None:
    source = ROOT / 'src/ada/compositions/manager_surface'
    commented = ROOT / 'commented/ada/compositions/manager_surface'

    for production in source.glob('*.py'):
        assert (commented / production.name).is_file()
