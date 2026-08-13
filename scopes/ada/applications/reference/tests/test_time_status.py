from ada.applications.reference.application import build_definition
from ada.contracts.tool_manifest import ToolManifestResolution
from ada.ui.shell.time_status import create_ada_time_status_module


def test_reference_application_registers_time_status_after_header() -> None:
    definition = build_definition()
    names = [module.name for module in definition.modules]

    assert 'ada-time-status' in names
    assert names.index('ada-header') < names.index('ada-time-status')
    assert create_ada_time_status_module().name == 'ada-time-status'


def test_reference_application_omits_time_status_without_tool_configuration() -> None:
    definition = build_definition(tool_manifest_resolution=ToolManifestResolution.not_projected())

    assert 'ada-time-status' not in [module.name for module in definition.modules]
