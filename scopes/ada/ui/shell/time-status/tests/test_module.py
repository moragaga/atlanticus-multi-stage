from ada.ui.shell.time_status import ADA_TIME_STATUS_ASSET_LAYER, create_ada_time_status_module


def test_time_status_module_declares_assets_without_server_callbacks() -> None:
    module = create_ada_time_status_module()

    assert module.name == 'ada-time-status'
    assert module.asset_layers == (ADA_TIME_STATUS_ASSET_LAYER,)
    assert ADA_TIME_STATUS_ASSET_LAYER.load_order == 275
    assert module.register_callbacks is None
