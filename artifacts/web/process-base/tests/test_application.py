from process_base.application import build_definition


def test_process_base_application_consumes_composition_modules() -> None:
    definition = build_definition()
    names = tuple(module.name for module in definition.modules)

    assert definition.metadata.application_id == 'ada-process-base'
    assert definition.page_packages == ('process_base.pages',)
    assert names[-1] == 'ada-process-composition'
    assert 'ada-dashboard' in names
    assert 'ada-alarms' in names
    assert 'ada-header' in names
    assert 'ada-process-layout' in names


def test_process_base_asset_load_orders_are_unique() -> None:
    definition = build_definition()
    layers = [layer for module in definition.modules for layer in module.asset_layers]
    layers.extend(definition.asset_layers)
    load_orders = tuple(layer.load_order for layer in layers)

    assert len(load_orders) == len(set(load_orders))
