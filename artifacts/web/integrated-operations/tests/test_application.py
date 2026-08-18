from integrated_operations.application import build_definition


def test_application_consumes_composition_as_portable_tool() -> None:
    definition = build_definition()
    orders = [layer.load_order for module in definition.modules for layer in module.asset_layers]
    orders.extend(layer.load_order for layer in definition.asset_layers)

    assert definition.metadata.application_id == 'ada-integrated-operations'
    assert definition.page_packages == ('integrated_operations.pages',)
    assert len(orders) == len(set(orders))
