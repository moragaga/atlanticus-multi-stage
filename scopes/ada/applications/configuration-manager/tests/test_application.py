from pathlib import Path

import pytest

pytest.importorskip('dash')

from ada.applications.configuration_manager.application import (
    TOOLS_WORKFLOW_SERVICE,
    build_configuration_manager_definition,
)
from ada.applications.configuration_manager.local import build_local_dependencies


def test_configuration_manager_starts_with_tools_as_root_configuration(tmp_path) -> None:
    definition = build_configuration_manager_definition(
        dependencies=build_local_dependencies(runtime_root=tmp_path),
        publications_root=Path('.runtime/assets'),
    )

    module = definition.modules[0]
    assert definition.current_path == '/tools'
    assert [item.key for item in definition.modules] == ['tools']
    assert module.workflow_service == TOOLS_WORKFLOW_SERVICE
    assert module.content_section_title == 'Configuración de herramienta'
    assert module.workflow_section_title == 'Estado y trazabilidad'
    assert module.source_name == 'Archivo local'
    assert module.projection_name == 'Archivo local'
    assert module.access.publish == 'tools.manage'


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
