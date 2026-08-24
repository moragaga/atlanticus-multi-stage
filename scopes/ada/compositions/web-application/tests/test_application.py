from types import SimpleNamespace

import pytest
from dash import html

import ada.compositions.web_application.definition as definition_module
import ada.compositions.web_application.presentation as presentation
from ada.compositions.surface import AdaSurfaceComposition, AdaSurfaceResolution
from ada.compositions.web_application import AdaApplicationComposition
from ada.contracts.tool_manifest import (
    ToolManifest,
    ToolManifestResolution,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
)
from atlanticus.web.services import ServiceRegistry


def _manifest() -> ToolManifest:
    return ToolManifest(
        tool_key='test_surface',
        display_name='Test Surface',
        sources=(ToolSource(key=ToolSourceKey.PI, stale_after_seconds=60),),
        sections=(
            ToolSection(
                key='body',
                display_name='Body',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.GLOBAL,
            ),
        ),
    )


def _composition(*, manager=None, administration_route_prefix='/administration'):
    operational = AdaSurfaceComposition(
        adapter_key='test-surface',
        manifest=_manifest(),
        modules=(),
        builder=lambda _services: html.Div(id='operational-tool'),
    )
    return AdaApplicationComposition(
        operational_resolution=AdaSurfaceResolution(
            configuration=ToolManifestResolution.not_projected(),
            surface=operational,
        ),
        manager=manager,
        administration_route_prefix=administration_route_prefix,
    )


def _props(component):
    return component.to_plotly_json()['props']


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


def test_application_composition_keeps_generic_operational_resolution() -> None:
    composition = _composition()

    assert composition.operational.adapter_key == 'test-surface'
    assert (
        composition.operational_resolution.configuration == ToolManifestResolution.not_projected()
    )
    assert composition.manager is None
    assert composition.administration_route_prefix == '/administration'


def test_application_composition_validates_administration_route_prefix() -> None:
    resolution = _composition().operational_resolution

    with pytest.raises(ValueError, match='absolute route prefix'):
        AdaApplicationComposition(
            operational_resolution=resolution,
            administration_route_prefix='administration',
        )


def test_application_layout_has_one_dynamic_surface_host_and_navigation(monkeypatch) -> None:
    services = ServiceRegistry()
    composition = _composition()
    navigation = html.Div(id='navigation-overlay')
    monkeypatch.setattr(
        presentation,
        'build_ada_navigation_offcanvas_from_services',
        lambda value: navigation if value is services else None,
    )

    layout = presentation.build_ada_application_layout(
        services,
        composition=composition,
    )
    nodes = tuple(_walk(layout))

    assert _props(layout)['data-ada-unified-application'] == 'true'
    assert sum(_props(node).get('id') == presentation.LOCATION_ID for node in nodes) == 1
    assert sum(_props(node).get('id') == presentation.SURFACE_HOST_ID for node in nodes) == 1
    assert sum(_props(node).get('id') == 'navigation-overlay' for node in nodes) == 1
    assert sum(_props(node).get('id') == 'operational-tool' for node in nodes) == 1


def test_operational_route_uses_resolved_surface_without_knowing_concrete_adapter() -> None:
    surface = presentation.build_application_surface(
        ServiceRegistry(),
        composition=_composition(),
        pathname='/',
    )
    nodes = tuple(_walk(surface))

    assert _props(surface)['data-ada-unified-surface'] == 'operational'
    assert _props(surface)['data-ada-surface-adapter'] == 'test-surface'
    assert any(_props(node).get('id') == 'operational-tool' for node in nodes)


def test_administration_route_delegates_to_optional_manager_composition() -> None:
    services = ServiceRegistry()
    expected = html.Div(id='manager-composition')
    captured = []

    manager = SimpleNamespace(
        web_modules=(),
        matches=lambda pathname: pathname == '/administration/tools',
        build=lambda value: captured.append(value) or expected,
    )

    surface = presentation.build_application_surface(
        services,
        composition=_composition(manager=manager),
        pathname='/administration/tools',
    )

    assert surface is expected
    assert captured == [services]


def test_unavailable_administration_does_not_replace_operational_baseline() -> None:
    surface = presentation.build_application_surface(
        ServiceRegistry(),
        composition=_composition(manager=None),
        pathname='/administration/tools',
    )

    props = _props(surface)
    assert props['data-ada-unified-surface'] == 'manager-unavailable'
    assert 'Volver a la aplicación' in str(props['children'])


def test_generic_definition_wires_shared_navigation_operational_and_optional_manager(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(definition_module, 'create_ada_navigation_module', lambda: 'ada-navigation')
    monkeypatch.setattr(
        definition_module,
        'create_ada_application_presentation_module',
        lambda _composition: 'ada-presentation',
    )
    manager = SimpleNamespace(web_modules=('manager-principal', 'manager-surface'))
    composition = SimpleNamespace(
        operational=SimpleNamespace(modules=('operational-module',)),
        manager=manager,
    )
    layer = object()
    metadata = SimpleNamespace()

    definition = definition_module.build_ada_web_definition(
        import_name='example_application',
        metadata=metadata,
        deployment_modules=('identity', 'users', 'authorization'),
        composition=composition,
        page_packages=('example.pages',),
        asset_layers=(layer,),
        flask_config={'SECRET_KEY': 'secret'},
    )

    assert definition.import_name == 'example_application'
    assert definition.metadata is metadata
    assert definition.modules == (
        'identity',
        'users',
        'authorization',
        'operational-module',
        'ada-navigation',
        'manager-principal',
        'manager-surface',
        'ada-presentation',
    )
    assert definition.page_packages == ('example.pages',)
    assert definition.asset_layers == (layer,)
    assert definition.publications_root == tmp_path / '.runtime' / 'assets'
    assert definition.flask_config == {'SECRET_KEY': 'secret'}
    assert definition.layout.keywords['composition'] is composition


def test_presentation_module_owns_generic_application_assets() -> None:
    module = presentation.create_ada_application_presentation_module(_composition())

    assert module.name == 'ada-unified-presentation'
    assert len(module.asset_layers) == 1
    layer = module.asset_layers[0]
    assert layer.name == 'ada_web_application'
    assert layer.load_order == 800
    assert layer.package == 'ada.compositions.web_application'
    assert layer.source_directory is None
