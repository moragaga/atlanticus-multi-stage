import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_commented_python_mirror_preserves_production_tokens() -> None:
    production = [ROOT / 'app.py', ROOT / 'gunicorn.conf.py', *(ROOT / 'src').rglob('*.py')]
    for source in production:
        if source.name == 'py.typed':
            continue
        relative = source.relative_to(ROOT)
        if relative.parts[0] == 'src':
            mirror = ROOT / 'commented' / Path(*relative.parts[1:])
        else:
            mirror = ROOT / 'commented' / relative
        assert mirror.is_file(), relative
        assert _tokens(source) == _tokens(mirror), relative


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
