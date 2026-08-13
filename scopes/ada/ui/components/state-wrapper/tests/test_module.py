from ada.ui.components.state_wrapper import (
    ADA_STATE_WRAPPER_ASSET_LAYER,
    create_ada_state_wrapper_module,
)


def test_state_wrapper_module_declares_its_asset_layer() -> None:
    module = create_ada_state_wrapper_module()

    assert module.name == 'ada-state-wrapper'
    assert module.asset_layers == (ADA_STATE_WRAPPER_ASSET_LAYER,)
    assert ADA_STATE_WRAPPER_ASSET_LAYER.load_order == 210
