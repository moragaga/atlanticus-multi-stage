from dataclasses import replace

from ada.applications.configuration_manager.local import build_local_dependencies
from ada.applications.configuration_manager.workflows import ToolManagerWorkflowAdapter
from ada.configuration.tools import (
    ToolConfigurationCatalog,
    integrated_operations_configuration_from_manifest,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from atlanticus.web.manager import ProjectionState, resolve_projection_state


def _catalog() -> ToolConfigurationCatalog:
    return ToolConfigurationCatalog(
        (
            integrated_operations_configuration_from_manifest(
                INTEGRATED_OPERATIONS_MANIFEST
            ),
        )
    )


def test_tool_adapter_exposes_draft_publish_projection_and_history(tmp_path) -> None:
    dependencies = build_local_dependencies(runtime_root=tmp_path)
    adapter = ToolManagerWorkflowAdapter(dependencies.tools)
    payload = _catalog().to_document()

    assert resolve_projection_state(adapter.get_status()) is ProjectionState.NO_SOURCE
    validation = adapter.validate_draft(payload)
    assert validation.valid
    assert resolve_projection_state(adapter.get_status()) is ProjectionState.NO_SOURCE

    publication = adapter.publish_draft(payload, None)
    assert publication.published
    assert resolve_projection_state(adapter.get_status()) is ProjectionState.READY

    projection = adapter.project(publication.source_revision)
    assert projection.projected
    assert resolve_projection_state(adapter.get_status()) is ProjectionState.SYNCHRONIZED
    assert adapter.list_history()[0].revision == publication.source_revision


def test_loading_historical_revision_does_not_mutate_source(tmp_path) -> None:
    dependencies = build_local_dependencies(runtime_root=tmp_path)
    adapter = ToolManagerWorkflowAdapter(dependencies.tools)
    first = adapter.publish_draft(_catalog().to_document(), None)
    current_tool = _catalog().tools[0]
    changed = ToolConfigurationCatalog(
        (replace(current_tool, display_name='Cambio temporal'),)
    )
    second = adapter.publish_draft(changed.to_document(), first.source_revision)

    loaded = adapter.load_revision(first.source_revision)

    assert ToolConfigurationCatalog.from_document(loaded) == _catalog()
    assert adapter.get_status().source_revision == second.source_revision
    assert len(adapter.list_history()) == 2


def test_local_dependencies_start_without_manifest_bootstrap(tmp_path) -> None:
    dependencies = build_local_dependencies(runtime_root=tmp_path)

    assert dependencies.tools.administration.load_source() is None
    assert dependencies.tools.projection.load() is None
