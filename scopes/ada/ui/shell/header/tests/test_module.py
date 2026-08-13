from ada.ui.shell.header import ADA_HEADER_ASSET_LAYER, create_ada_header_module


def test_header_module_declares_only_header_assets() -> None:
    module = create_ada_header_module()

    assert module.name == 'ada-header'
    assert module.asset_layers == (ADA_HEADER_ASSET_LAYER,)
    assert ADA_HEADER_ASSET_LAYER.load_order == 250
    assert ADA_HEADER_ASSET_LAYER.package == 'ada.ui.shell.header'
