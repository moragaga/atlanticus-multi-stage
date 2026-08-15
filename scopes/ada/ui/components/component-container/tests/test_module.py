from ada.ui.components.component_container import (
    ADA_COMPONENT_CONTAINER_ASSET_LAYER,
    create_ada_component_container_module,
)


def test_component_container_module_registers_assets() -> None:
    module = create_ada_component_container_module()

    assert module.name == 'ada-component-container'
    assert module.asset_layers == (ADA_COMPONENT_CONTAINER_ASSET_LAYER,)
    assert ADA_COMPONENT_CONTAINER_ASSET_LAYER.load_order == 226
