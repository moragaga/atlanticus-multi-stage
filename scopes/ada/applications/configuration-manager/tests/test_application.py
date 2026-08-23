from pathlib import Path

import pytest

pytest.importorskip('dash')

from ada.applications.configuration_manager.application import (
    build_configuration_manager_definition,
)
from ada.applications.configuration_manager.local import build_local_dependencies
from atlanticus.web.manager.application import build_manager_web_definition


def test_configuration_manager_preview_wraps_reusable_surface(tmp_path) -> None:
    definition = build_configuration_manager_definition(
        dependencies=build_local_dependencies(runtime_root=tmp_path),
        publications_root=Path('.runtime/assets'),
    )
    surface = definition.surface
    tools, users, navigation = surface.modules

    assert definition.metadata.version == '0.2.12'
    assert surface.default_module_key == 'tools'
    assert surface.route_prefix == ''
    assert [item.key for item in surface.modules] == ['tools', 'users', 'navigation']
    assert tools.route == '/tools'
    assert users.route == '/users'
    assert navigation.route == '/navigation'
    assert tools.content_section_title == 'Configuración de herramienta'
    assert users.content_section_title == 'Usuarios y perfiles'
    assert navigation.content_section_title == 'Navegación'
    assert tools.workflow_section_title == 'Estado y trazabilidad'
    assert users.workflow_section_title == 'Estado y trazabilidad'
    assert tools.source_name == 'Archivo local'
    assert users.source_name == 'Archivo local'
    assert users.projection_name == 'Archivo local'
    assert navigation.source_name == 'Archivo local'
    assert navigation.projection_name == 'Archivo local'
    assert tools.access.publish == 'tools.manage'
    assert users.access.publish == 'users.manage'
    assert navigation.access.publish == 'navigation.manage'


def test_configuration_manager_keeps_standalone_brand_and_navigation_slots(tmp_path) -> None:
    definition = build_configuration_manager_definition(
        dependencies=build_local_dependencies(runtime_root=tmp_path),
        publications_root=Path('.runtime/assets'),
    )

    assert [mark.role for mark in definition.brand.marks] == [
        'product',
        'framework',
        'organization',
    ]
    assert definition.header_actions is not None
    assert definition.shell_overlays is not None
    assert 'Cinzel' in definition.dash.external_stylesheets[0]


def test_configuration_manager_standalone_host_registers_pages_separately(tmp_path) -> None:
    definition = build_configuration_manager_definition(
        dependencies=build_local_dependencies(runtime_root=tmp_path),
        publications_root=tmp_path / 'assets',
    )
    web_definition = build_manager_web_definition(definition)
    module_by_name = {module.name: module for module in web_definition.modules}
    load_orders = [
        layer.load_order for module in web_definition.modules for layer in module.asset_layers
    ]

    assert module_by_name['manager-standalone-host'].page_packages == (
        'atlanticus.web.manager.pages',
    )
    assert module_by_name['manager-surface'].page_packages == ()
    assert len(load_orders) == len(set(load_orders))
