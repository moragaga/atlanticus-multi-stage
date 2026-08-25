from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/ada/runtime/delivery_cache'
COMMENTED = ROOT / 'commented/ada/runtime/delivery_cache'


def test_package_does_not_depend_on_dash_flask_or_cosmos() -> None:
    productive = '\n'.join(path.read_text(encoding='utf-8') for path in SOURCE.glob('*.py'))

    assert 'dash' not in productive.lower()
    assert 'flask' not in productive.lower()
    assert 'cosmos' not in productive.lower()


def test_commented_mirror_matches_productive_ast() -> None:
    source_files = sorted(path.relative_to(SOURCE) for path in SOURCE.glob('*.py'))
    commented_files = sorted(path.relative_to(COMMENTED) for path in COMMENTED.glob('*.py'))

    assert source_files == commented_files
    for relative_path in source_files:
        productive = ast.dump(
            ast.parse((SOURCE / relative_path).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        commented = ast.dump(
            ast.parse((COMMENTED / relative_path).read_text(encoding='utf-8')),
            include_attributes=False,
        )
        assert commented == productive
