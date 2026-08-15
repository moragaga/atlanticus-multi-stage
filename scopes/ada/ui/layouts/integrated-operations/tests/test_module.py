from ada.ui.layouts.integrated_operations import (
    ADA_INTEGRATED_OPERATIONS_LAYOUT_ASSET_LAYER,
    create_ada_integrated_operations_layout_module,
)


def test_layout_module_declares_its_asset_layer() -> None:
    module = create_ada_integrated_operations_layout_module()

    assert module.name == 'ada-integrated-operations-layout'
    assert module.asset_layers == (ADA_INTEGRATED_OPERATIONS_LAYOUT_ASSET_LAYER,)
    assert ADA_INTEGRATED_OPERATIONS_LAYOUT_ASSET_LAYER.load_order == 240
