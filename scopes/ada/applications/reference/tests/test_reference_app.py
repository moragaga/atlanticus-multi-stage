from ada.applications.reference.application import build_definition
from ada.applications.reference.navigation import build_reference_navigation
from ada.ui.components.global_indicator import ADA_GLOBAL_INDICATOR_ASSET_LAYER
from ada.ui.components.state_wrapper import ADA_STATE_WRAPPER_ASSET_LAYER
from ada.ui.framework.core import ADA_UI_ASSET_LAYER
from ada.ui.shell.header import ADA_HEADER_ASSET_LAYER
from ada.ui.shell.navigation import ADA_NAVIGATION_ASSET_LAYER
from atlanticus.web.navigation import NavigationDefinition


def test_reference_composes_runtime_and_transversal_components_in_order() -> None:
    definition = build_definition()
    modules = {module.name: module for module in definition.modules}

    assert definition.import_name == 'ada.applications.reference'
    assert definition.metadata.application_id == 'ada-ui-reference'
    assert tuple(modules) == (
        'users',
        'identity',
        'navigation',
        'ada-runtime',
        'ada-ui',
        'ada-navigation',
        'ada-state-wrapper',
        'ada-global-indicator',
        'ada-header',
        'reference',
    )
    assert modules['navigation'].asset_layers == ()
    assert modules['ada-runtime'].asset_layers == ()
    assert modules['ada-ui'].asset_layers == (ADA_UI_ASSET_LAYER,)
    assert modules['ada-navigation'].asset_layers == (ADA_NAVIGATION_ASSET_LAYER,)
    assert modules['ada-state-wrapper'].asset_layers == (ADA_STATE_WRAPPER_ASSET_LAYER,)
    assert modules['ada-global-indicator'].asset_layers == (ADA_GLOBAL_INDICATOR_ASSET_LAYER,)
    assert modules['ada-header'].asset_layers == (ADA_HEADER_ASSET_LAYER,)
    assert ADA_STATE_WRAPPER_ASSET_LAYER.load_order < ADA_GLOBAL_INDICATOR_ASSET_LAYER.load_order
    assert ADA_GLOBAL_INDICATOR_ASSET_LAYER.load_order < ADA_HEADER_ASSET_LAYER.load_order
    assert modules['reference'].asset_layers[0].load_order == 900
    assert modules['reference'].asset_layers[0].package == 'ada.applications.reference'


def test_reference_navigation_is_definition_not_user_specific_menu() -> None:
    definition = build_reference_navigation()

    assert isinstance(definition, NavigationDefinition)
    assert definition.links[0].href == '/'
    assert definition.groups[0].links[0].href == '/status'

