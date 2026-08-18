from pathlib import Path

import pytest

pytest.importorskip('dash')

from ada.applications.configuration_manager.application import (
    TOOLS_WORKFLOW_SERVICE,
    USERS_WORKFLOW_SERVICE,
    build_configuration_manager_definition,
)
from ada.applications.configuration_manager.local import build_local_dependencies


def test_configuration_manager_registers_tools_and_users(tmp_path) -> None:
    definition = build_configuration_manager_definition(
        dependencies=build_local_dependencies(runtime_root=tmp_path),
        publications_root=Path('.runtime/assets'),
    )

    tools, users = definition.modules
    assert definition.current_path == '/tools'
    assert [item.key for item in definition.modules] == ['tools', 'users']
    assert tools.route == '/tools'
    assert users.route == '/users'
    assert tools.workflow_service == TOOLS_WORKFLOW_SERVICE
    assert users.workflow_service == USERS_WORKFLOW_SERVICE
    assert tools.content_section_title == 'Configuración de herramienta'
    assert users.content_section_title == 'Usuarios y perfiles'
    assert tools.workflow_section_title == 'Estado y trazabilidad'
    assert users.workflow_section_title == 'Estado y trazabilidad'
    assert tools.source_name == 'Archivo local'
    assert users.source_name == 'Archivo local'
    assert users.projection_name == 'Archivo local'
    assert tools.access.publish == 'tools.manage'
    assert users.access.publish == 'users.manage'


def test_configuration_manager_keeps_atlanticus_brand_and_navigation_slots(tmp_path) -> None:
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
