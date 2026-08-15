from ada.ui.components.component_card import (
    ADA_COMPONENT_CARD_ASSET_LAYER,
    create_ada_component_card_module,
)


def test_component_card_module_declares_its_asset_layer() -> None:
    module = create_ada_component_card_module()

    assert module.name == 'ada-component-card'
    assert module.asset_layers == (ADA_COMPONENT_CARD_ASSET_LAYER,)
    assert ADA_COMPONENT_CARD_ASSET_LAYER.load_order == 230
