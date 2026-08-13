import pytest

from ada.applications.reference.application import build_definition
from ada.applications.reference.navigation import build_reference_navigation
from ada.contracts.tool_manifest import ToolManifestResolution
from ada.ui.components.global_indicator import ADA_GLOBAL_INDICATOR_ASSET_LAYER
from ada.ui.components.state_wrapper import ADA_STATE_WRAPPER_ASSET_LAYER
from ada.ui.framework.core import ADA_UI_ASSET_LAYER
from ada.ui.shell.header import ADA_HEADER_ASSET_LAYER
from ada.ui.shell.navigation import ADA_NAVIGATION_ASSET_LAYER
from ada.ui.shell.time_status import ADA_TIME_STATUS_ASSET_LAYER
from atlanticus.web.navigation import NavigationDefinition
from atlanticus.web.services import ServiceRegistry


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
        'ada-time-status',
        'reference',
    )
    assert modules['navigation'].asset_layers == ()
    assert modules['ada-runtime'].asset_layers == ()
    assert modules['ada-ui'].asset_layers == (ADA_UI_ASSET_LAYER,)
    assert modules['ada-navigation'].asset_layers == (ADA_NAVIGATION_ASSET_LAYER,)
    assert modules['ada-state-wrapper'].asset_layers == (ADA_STATE_WRAPPER_ASSET_LAYER,)
    assert modules['ada-global-indicator'].asset_layers == (ADA_GLOBAL_INDICATOR_ASSET_LAYER,)
    assert modules['ada-header'].asset_layers == (ADA_HEADER_ASSET_LAYER,)
    assert modules['ada-time-status'].asset_layers == (ADA_TIME_STATUS_ASSET_LAYER,)
    assert ADA_STATE_WRAPPER_ASSET_LAYER.load_order < ADA_GLOBAL_INDICATOR_ASSET_LAYER.load_order
    assert ADA_GLOBAL_INDICATOR_ASSET_LAYER.load_order < ADA_HEADER_ASSET_LAYER.load_order
    assert ADA_HEADER_ASSET_LAYER.load_order < ADA_TIME_STATUS_ASSET_LAYER.load_order
    assert modules['reference'].asset_layers[0].load_order == 900
    assert modules['reference'].asset_layers[0].package == 'ada.applications.reference'


@pytest.mark.parametrize(
    ('resolution', 'cover', 'message'),
    (
        (
            ToolManifestResolution.not_projected(),
            'construction',
            'The basic configuration for this tool is not available yet.',
        ),
        (
            ToolManifestResolution.invalid(),
            'source-error',
            'The basic configuration for this tool is invalid.',
        ),
        (
            ToolManifestResolution.source_error(),
            'source-error',
            'The basic configuration for this tool could not be loaded.',
        ),
    ),
)
def test_reference_degrades_to_ready_configuration_wrapper(resolution, cover, message) -> None:
    definition = build_definition(tool_manifest_resolution=resolution)

    assert tuple(module.name for module in definition.modules) == (
        'users',
        'identity',
        'navigation',
        'ada-ui',
        'ada-state-wrapper',
        'reference',
    )

    layout = definition.layout(ServiceRegistry())
    components = _walk(layout)
    configuration_wrapper = next(
        component
        for component in components
        if _props(component).get('data-ready-name') == 'tool-configuration'
    )

    assert _props(layout)['data-ready-required'] == 'tool-configuration'
    assert _props(configuration_wrapper)['data-ready'] == 'true'
    assert _props(configuration_wrapper)['data-cover'] == cover
    assert message in _text(layout)


def test_reference_navigation_is_definition_not_user_specific_menu() -> None:
    definition = build_reference_navigation()

    assert isinstance(definition, NavigationDefinition)
    assert definition.links[0].href == '/'
    assert definition.groups[0].links[0].href == '/status'


def _walk(component):
    yield component
    children = _props(component).get('children')
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = (children,)
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def _props(component) -> dict[str, object]:
    return component.to_plotly_json()['props']


def _text(component) -> str:
    values: list[str] = []

    def visit(value) -> None:
        if isinstance(value, str):
            values.append(value)
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                visit(item)
            return
        if hasattr(value, 'to_plotly_json'):
            visit(_props(value).get('children'))

    visit(component)
    return ' '.join(values)
