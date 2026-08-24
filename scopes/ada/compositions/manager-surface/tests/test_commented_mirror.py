import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _tokens(path: Path):
    result = []
    for token in tokenize.generate_tokens(io.StringIO(path.read_text(encoding='utf-8')).readline):
        if token.type in {tokenize.COMMENT, tokenize.NL, tokenize.ENCODING}:
            continue
        if token.type == tokenize.NEWLINE and not token.string.strip():
            continue
        result.append((token.type, token.string))
    return result


def test_commented_python_mirror_preserves_production_tokens() -> None:
    source = ROOT / 'src/ada/compositions/manager_surface'
    commented = ROOT / 'commented/ada/compositions/manager_surface'

    for production in source.glob('*.py'):
        mirror = commented / production.name
        assert mirror.is_file(), production.name
        assert _tokens(production) == _tokens(mirror), production.name
