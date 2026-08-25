from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'ada' / 'ui' / 'runtime_kpi'


def test_generic_runtime_ui_does_not_hardcode_surface_component_names() -> None:
    source = '\n'.join(path.read_text(encoding='utf-8') for path in SRC.glob('*.py'))

    assert 'global_indicators' not in source
    assert 'molienda' not in source
    assert 'integrated_operations' not in source


def test_generic_runtime_ui_does_not_access_cosmos_or_worker_cache() -> None:
    source = '\n'.join(path.read_text(encoding='utf-8') for path in SRC.glob('*.py'))

    assert 'Cosmos' not in source
    assert 'WorkerDeliveryCache' not in source
    assert 'delivery_cache' not in source
    assert 'delivery_collector' not in source


def test_generic_runtime_ui_uses_string_store_ids_not_pattern_matching() -> None:
    source = (SRC / 'callbacks.py').read_text(encoding='utf-8')

    assert 'MATCH' not in source
    assert 'ALL' not in source
    assert 'ALLSMALLER' not in source
