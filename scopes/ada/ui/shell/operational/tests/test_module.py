from ada.ui.shell.operational import (
    ADA_OPERATIONAL_SHELL_ASSET_LAYER,
    create_ada_operational_shell_module,
)


def test_operational_shell_module_exposes_single_asset_layer() -> None:
    module = create_ada_operational_shell_module()

    assert module.name == 'ada-operational-shell'
    assert module.asset_layers == (ADA_OPERATIONAL_SHELL_ASSET_LAYER,)
    assert ADA_OPERATIONAL_SHELL_ASSET_LAYER.load_order == 255
