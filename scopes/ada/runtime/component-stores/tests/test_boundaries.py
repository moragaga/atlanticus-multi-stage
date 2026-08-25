import ast
from pathlib import Path


def test_runtime_component_stores_do_not_own_collector_or_data_source_dependencies() -> None:
    package = Path(__file__).parents[1]
    source = '\n'.join(
        path.read_text(encoding='utf-8')
        for path in package.glob('src/ada/runtime/component_stores/*.py')
    )

    assert 'Cosmos' not in source
    assert 'WorkerDeliveryCache' not in source
    assert '@callback' not in source
    assert '@app.callback' not in source


def test_commented_mirrors_match_productive_ast() -> None:
    package = Path(__file__).parents[1]
    for name in ('errors.py', 'registry.py', 'mount.py', '__init__.py'):
        productive = ast.dump(
            ast.parse(package.joinpath('src/ada/runtime/component_stores', name).read_text()),
            include_attributes=False,
        )
        commented = ast.dump(
            ast.parse(package.joinpath('commented/ada/runtime/component_stores', name).read_text()),
            include_attributes=False,
        )
        assert commented == productive, name
