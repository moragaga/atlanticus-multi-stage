import io
import tokenize
from pathlib import Path


def _tokens(path: Path) -> list[tuple[int, str]]:
    ignored = {
        tokenize.COMMENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.NL,
        tokenize.NEWLINE,
    }
    return [
        (token.type, token.string)
        for token in tokenize.generate_tokens(io.StringIO(path.read_text()).readline)
        if token.type not in ignored
    ]


def test_commented_mirror_matches_production_tokens() -> None:
    package_root = Path(__file__).parents[1]
    production = package_root / 'src/ada/configuration/kpis'
    commented = package_root / 'commented/ada/configuration/kpis'

    production_files = sorted(path.relative_to(production) for path in production.rglob('*.py'))
    commented_files = sorted(path.relative_to(commented) for path in commented.rglob('*.py'))

    assert commented_files == production_files
    for relative_path in production_files:
        assert _tokens(production / relative_path) == _tokens(commented / relative_path)
