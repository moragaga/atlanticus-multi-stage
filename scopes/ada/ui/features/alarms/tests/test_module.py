from ada.ui.features.alarms import ADA_ALARMS_ASSET_LAYER, create_ada_alarms_module


def test_alarms_module_publishes_feature_assets() -> None:
    module = create_ada_alarms_module()

    assert module.name == 'ada-alarms'
    assert module.asset_layers == (ADA_ALARMS_ASSET_LAYER,)
    assert ADA_ALARMS_ASSET_LAYER.name == 'ada_ui_alarms'
    assert ADA_ALARMS_ASSET_LAYER.load_order == 260
    assert ADA_ALARMS_ASSET_LAYER.package == 'ada.ui.features.alarms'
