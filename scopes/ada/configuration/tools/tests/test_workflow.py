from dataclasses import replace

import pytest

from ada.configuration.tools import (
    ToolConfiguration,
    ToolConfigurationKind,
    compose_tool_configuration_services,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters.memory import (
    MemoryToolConfigurationStore,
    MemoryToolProjectionRepository,
)
from ada.configuration.tools.errors import (
    ToolConfigurationProjectionError,
    ToolConfigurationValidationError,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


def _configuration() -> ToolConfiguration:
    return integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST)


def _services():
    source = MemoryToolConfigurationStore()
    projection = MemoryToolProjectionRepository()
    services = compose_tool_configuration_services(
        source=source,
        publisher=source,
        projection=projection,
        audit_actor_provider=lambda: 'Admin',
    )
    return services, source, projection


def test_draft_validation_is_ephemeral_and_does_not_publish_source() -> None:
    services, source, _projection = _services()

    result = services.administration.validate_configuration(_configuration())

    assert result.valid is True
    assert source.fetch_bundle() is None
    assert source.list_history() == ()


def test_publish_revalidates_and_creates_first_source_history_version() -> None:
    services, source, _projection = _services()

    result = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )

    assert result.published is True
    assert source.fetch_bundle().revision == result.source_revision
    assert [item.revision for item in source.list_history()] == [result.source_revision]


def test_republishing_identical_content_is_idempotent() -> None:
    services, source, _projection = _services()
    first = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )

    second = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=first.source_revision,
    )

    assert second.published is False
    assert second.source_revision == first.source_revision
    assert len(source.list_history()) == 1


def test_publish_rejects_stale_source_revision() -> None:
    services, source, _projection = _services()
    first = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )
    changed = replace(_configuration(), display_name='Revision actual')
    services.administration.publish_configuration(
        changed,
        expected_source_revision=first.source_revision,
    )

    stale = replace(_configuration(), display_name='Revision obsoleta')
    with pytest.raises(
        ToolConfigurationValidationError,
        match='source revision changed before source publication',
    ):
        services.administration.publish_configuration(
            stale,
            expected_source_revision=first.source_revision,
        )
    assert source.fetch_bundle().configuration.display_name == 'Revision actual'


def test_projection_revalidates_published_source_and_writes_runtime_manifest() -> None:
    services, _source, projection = _services()
    publication = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )

    result = services.projection_workflow.project(publication.source_revision)

    assert result.projected is True
    assert projection.active is not None
    assert projection.active.manifest == INTEGRATED_OPERATIONS_MANIFEST


def test_projection_rejects_stale_expected_source_revision() -> None:
    services, _source, _projection = _services()
    first = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )
    changed = replace(_configuration(), display_name='Nueva fuente')
    services.administration.publish_configuration(
        changed,
        expected_source_revision=first.source_revision,
    )

    with pytest.raises(ToolConfigurationProjectionError, match='changed before projection'):
        services.projection_workflow.project(first.source_revision)


def test_incomplete_configuration_can_be_validated_but_cannot_be_published() -> None:
    services, source, _projection = _services()
    incomplete = ToolConfiguration(
        tool_key='process',
        display_name='Process',
        kind=ToolConfigurationKind.PROCESS,
    )

    validation = services.administration.validate_configuration(incomplete)

    assert validation.valid is False
    assert source.fetch_bundle() is None
    with pytest.raises(ToolConfigurationValidationError, match='must be valid'):
        services.administration.publish_configuration(
            incomplete,
            expected_source_revision=None,
        )


def test_historical_revision_is_loaded_without_changing_source() -> None:
    services, source, _projection = _services()
    first = services.administration.publish_configuration(
        _configuration(),
        expected_source_revision=None,
    )
    changed = replace(_configuration(), display_name='Cambio temporal')
    second = services.administration.publish_configuration(
        changed,
        expected_source_revision=first.source_revision,
    )

    loaded = services.administration.load_revision_configuration(first.source_revision)

    assert loaded == _configuration()
    assert source.fetch_bundle().revision == second.source_revision
    assert len(source.list_history()) == 2
