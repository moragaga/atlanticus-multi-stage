from ada.compositions.integrated_operations import (
    ADA_INTEGRATED_OPERATIONS_COMPOSITION_ASSET_LAYER,
    create_integrated_operations_tool_composition,
    create_integrated_operations_tool_modules,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


def test_integrated_operations_composition_owns_distinct_asset_layer() -> None:
    assert ADA_INTEGRATED_OPERATIONS_COMPOSITION_ASSET_LAYER.load_order == 281


def test_tool_modules_have_unique_asset_load_orders() -> None:
    composition = create_integrated_operations_tool_composition(INTEGRATED_OPERATIONS_MANIFEST)
    modules = create_integrated_operations_tool_modules(composition)
    orders = [layer.load_order for module in modules for layer in module.asset_layers]

    assert len(orders) == len(set(orders))
