from ada.ui.core import ADA_UI_ASSET_LAYER
from ada.ui.navigation import ADA_NAVIGATION_ASSET_LAYER
from ada_ui_reference.application import build_definition
from ada_ui_reference.navigation import build_reference_navigation


def test_reference_composes_generic_navigation_with_ada_presentation() -> None:
    definition = build_definition()
    modules = {module.name: module for module in definition.modules}

    assert tuple(modules) == ('navigation', 'ada-ui', 'ada-navigation', 'reference')
    assert modules['navigation'].asset_layers == ()
    assert modules['ada-ui'].asset_layers == (ADA_UI_ASSET_LAYER,)
    assert modules['ada-navigation'].asset_layers == (ADA_NAVIGATION_ASSET_LAYER,)
    assert modules['reference'].asset_layers[0].load_order == 900


def test_reference_menu_contains_root_link_and_group() -> None:
    menu = build_reference_navigation()

    assert menu.links[0].href == '/'
    assert menu.groups[0].links[0].href == '/status'
