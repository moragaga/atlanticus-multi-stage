from ada.ui.layouts.process import (
    ADA_PROCESS_LAYOUT_ASSET_LAYER,
    create_ada_process_layout_module,
)


def test_process_layout_module_exports_asset_layer() -> None:
    module = create_ada_process_layout_module()

    assert module.name == 'ada-process-layout'
    assert module.asset_layers == (ADA_PROCESS_LAYOUT_ASSET_LAYER,)
    assert ADA_PROCESS_LAYOUT_ASSET_LAYER.load_order == 241
