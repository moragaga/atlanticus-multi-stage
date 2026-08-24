from datetime import UTC, datetime

from ada.configuration.tools.adapters.file import (
    FileToolConfigurationSettings,
    FileToolConfigurationStore,
    FileToolProjectionRepository,
    FileToolProjectionSettings,
)
from ada.configuration.tools.adapters.memory import (
    MemoryToolConfigurationStore,
    MemoryToolProjectionRepository,
)
from ada.configuration.tools.builder import build_tool_manifest
from ada.configuration.tools.bundle import ToolConfigurationBundle
from ada.configuration.tools.models import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
)
from ada.configuration.tools.projection import ToolConfigurationProjection
from ada.configuration.tools.services import compose_tool_configuration_services
from ada.contracts.tool_manifest import ProcessBodySection, ToolScope, ToolSourceKey


def _configuration() -> ToolConfiguration:
    return ToolConfiguration(
        tool_key='flotacion',
        display_name='Flotación',
        kind=ToolConfigurationKind.PROCESS,
        operational_scope=ToolScope.PLANT,
        sources=(ToolSourceConfiguration(ToolSourceKey.PI, 300),),
        components=(
            ToolComponentConfiguration(
                key='flotacion',
                display_name='Flotación',
                layout_role=ProcessBodySection.CENTER,
                subcomponents=(
                    ToolSubcomponentConfiguration(
                        key='colectiva',
                        display_name='Colectiva',
                    ),
                ),
            ),
        ),
    )


def test_file_source_uses_one_document_and_unique_history_by_revision(tmp_path) -> None:
    root = tmp_path / 'source'
    store = FileToolConfigurationStore(FileToolConfigurationSettings(root=root))
    bundle = ToolConfigurationBundle.create(
        configuration=_configuration(),
        saved_by='tester',
        now_utc=datetime(2026, 8, 18, 14, 0, tzinfo=UTC),
    )

    store.publish_bundle(bundle, expected_source_revision=None)
    store.publish_bundle(
        ToolConfigurationBundle.create(configuration=_configuration(), saved_by='tester-2'),
        expected_source_revision=bundle.revision,
    )

    assert store.fetch_bundle() == bundle
    assert store.list_history() == (bundle,)
    assert store.fetch_revision(bundle.revision) == bundle
    assert [path.name for path in root.iterdir()] == ['tool_configuration.json.gz']


def test_file_projection_persists_only_runtime_projection(tmp_path) -> None:
    repository = FileToolProjectionRepository(
        FileToolProjectionSettings(root=tmp_path / 'projection')
    )
    projection = ToolConfigurationProjection.create(
        source_revision='source-revision',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 18, 14, 5, tzinfo=UTC),
        manifest=build_tool_manifest(_configuration()),
    )

    repository.save(projection)

    assert repository.load() == projection
    assert repository.health_check() is True
    assert [path.name for path in (tmp_path / 'projection').iterdir()] == ['tool.json']


def test_file_source_can_project_into_memory_repository(tmp_path) -> None:
    source = FileToolConfigurationStore(FileToolConfigurationSettings(root=tmp_path / 'source'))
    services = compose_tool_configuration_services(
        source=source,
        publisher=source,
        projection=MemoryToolProjectionRepository(),
        audit_actor_provider=lambda: 'tester',
    )
    publication = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )

    result = services.projection_workflow.project(publication.source_revision)

    assert result.projected is True


def test_memory_source_can_project_into_file_repository(tmp_path) -> None:
    source = MemoryToolConfigurationStore()
    projection = FileToolProjectionRepository(
        FileToolProjectionSettings(root=tmp_path / 'projection')
    )
    services = compose_tool_configuration_services(
        source=source,
        publisher=source,
        projection=projection,
        audit_actor_provider=lambda: 'tester',
    )
    publication = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )

    services.projection_workflow.project(publication.source_revision)

    assert projection.load() is not None
    assert projection.load().source_revision == publication.source_revision
