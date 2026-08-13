from pathlib import Path

from ada.ui.features.alarms import ADA_ALARMS_ASSET_LAYER, create_ada_alarms_module


def test_alarms_module_publishes_feature_assets() -> None:
    module = create_ada_alarms_module()

    assert module.name == 'ada-alarms'
    assert module.asset_layers == (ADA_ALARMS_ASSET_LAYER,)
    assert ADA_ALARMS_ASSET_LAYER.name == 'ada_ui_alarms'
    assert ADA_ALARMS_ASSET_LAYER.load_order == 260
    assert ADA_ALARMS_ASSET_LAYER.package == 'ada.ui.features.alarms'


def test_alarms_asset_lists_publish_dashboard_layers_in_order() -> None:
    resources = (
        Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'features' / 'alarms' / 'resources'
    )

    assert (resources / 'css' / 'css.list').read_text(encoding='utf-8').splitlines() == [
        '10-header-presentations.css',
        '20-dashboard-baseline.css',
        '30-dashboard-routes.css',
        '40-impact.css',
    ]
    assert (resources / 'js' / 'js.list').read_text(encoding='utf-8').splitlines() == [
        '10-dashboard-geometry.js',
        '20-dashboard-routes.js',
    ]
