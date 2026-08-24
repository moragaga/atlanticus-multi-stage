import io
import tokenize
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/ada/compositions/web_application'
COMMENTED = ROOT / 'commented/ada/compositions/web_application'


def test_generic_application_has_no_concrete_surface_or_configuration_authority() -> None:
    content = '\n'.join(path.read_text(encoding='utf-8') for path in SOURCE.rglob('*.py'))

    for forbidden in (
        'IntegratedOperationsSurfaceAdapter',
        'ProcessSurfaceAdapter',
        'ProcessToolComposition',
        'INTEGRATED_OPERATIONS_MANIFEST',
        'ToolManifestResolution',
        "'/manager'",
        '"/manager"',
    ):
        assert forbidden not in content


def test_manager_is_not_a_runtime_dependency_of_generic_application() -> None:
    document = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = set(document['project']['dependencies'])

    assert 'ada-composition-surface==0.1.0' in dependencies
    assert 'ada-ui-shell-navigation==0.1.0' in dependencies
    assert 'ada-composition-manager-surface==0.1.0' not in dependencies
    assert all('integrated-operations' not in dependency for dependency in dependencies)
    assert all('process' not in dependency for dependency in dependencies)


def test_generic_application_assets_are_packaged_and_declared() -> None:
    css = SOURCE / 'resources/css'

    assert (css / '10-unified-application.css').is_file()
    assert (css / 'css.list').read_text(encoding='utf-8').splitlines() == [
        '10-unified-application.css'
    ]


def test_commented_python_mirror_preserves_production_tokens() -> None:
    source_files = sorted(path.relative_to(SOURCE) for path in SOURCE.rglob('*.py'))
    commented_files = sorted(path.relative_to(COMMENTED) for path in COMMENTED.rglob('*.py'))

    assert source_files == commented_files
    for relative in source_files:
        assert _tokens(SOURCE / relative) == _tokens(COMMENTED / relative), relative


def _tokens(path: Path) -> list[tuple[int, str]]:
    ignored = {
        tokenize.COMMENT,
        tokenize.ENCODING,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
    }
    return [
        (token.type, token.string)
        for token in tokenize.generate_tokens(
            io.StringIO(path.read_text(encoding='utf-8')).readline
        )
        if token.type not in ignored
    ]
