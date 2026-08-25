from pathlib import Path

PACKAGE = Path(__file__).parents[1]
SOURCE = PACKAGE / 'src' / 'ada' / 'runtime' / 'delivery_collector'


def test_collector_does_not_depend_on_cosmos_flask_or_ui_renderers() -> None:
    text = '\n'.join(path.read_text(encoding='utf-8') for path in SOURCE.glob('*.py'))

    assert 'azure.cosmos' not in text
    assert 'CosmosClient' not in text
    assert 'from flask' not in text
    assert 'html.Img' not in text
    assert 'value_kind' not in text


def test_collector_uses_r1_cache_and_r3_registry_as_explicit_dependencies() -> None:
    callbacks = (SOURCE / 'callbacks.py').read_text(encoding='utf-8')
    distribution = (SOURCE / 'distribution.py').read_text(encoding='utf-8')

    assert 'WorkerDeliveryCache' in callbacks
    assert 'RuntimeComponentStoreRegistry' in distribution
    assert 'DeliveryChannel.LATEST' in callbacks
    assert 'DeliveryChannel.TIMESERIES' in callbacks
