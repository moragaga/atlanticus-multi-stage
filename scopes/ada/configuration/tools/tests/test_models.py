from dataclasses import replace

import pytest

from ada.configuration.tools import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
    build_identity_key,
)
from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.contracts.tool_manifest import ToolScope, ToolSourceKey


def test_identity_is_generated_from_display_name_but_is_not_recomputed_on_rename() -> None:
    key = build_identity_key('Transporte de Fluidos')
    original = ToolConfiguration(
        tool_key=key,
        display_name='Transporte de Fluidos',
        kind=ToolConfigurationKind.PROCESS,
    )

    renamed = replace(original, display_name='Transporte de Fluidos Planta')

    assert key == 'transporte_de_fluidos'
    assert renamed.tool_key == 'transporte_de_fluidos'


def test_configuration_roundtrip_preserves_order_and_stable_ids() -> None:
    configuration = ToolConfiguration(
        tool_key='integrated_operations',
        display_name='Operaciones Integradas',
        kind=ToolConfigurationKind.INTEGRATED_OPERATIONS,
        sources=(ToolSourceConfiguration(ToolSourceKey.PI, 300),),
        components=(
            ToolComponentConfiguration(
                key='flotacion',
                display_name='Flotación',
                scope=ToolScope.PLANT,
                subcomponents=(
                    ToolSubcomponentConfiguration(
                        key='colectiva',
                        display_name='Colectiva',
                    ),
                    ToolSubcomponentConfiguration(
                        key='selectiva',
                        display_name='Selectiva',
                    ),
                ),
            ),
        ),
    )

    restored = ToolConfiguration.from_document(configuration.to_document())

    assert restored == configuration


def test_source_document_rejects_boolean_freshness() -> None:
    with pytest.raises(ToolConfigurationValidationError, match='contract is invalid'):
        ToolSourceConfiguration.from_document({'key': 'pi', 'stale_after_seconds': True})


def test_public_contract_exposes_one_tool_without_catalog_or_manifest_registry() -> None:
    import ada.configuration.tools as tools

    assert not hasattr(tools, 'ToolConfigurationCatalog')
    assert not hasattr(tools, 'build_tool_manifest_registry')


def test_single_tool_documents_use_configuration_and_manifest_roots() -> None:
    from datetime import UTC, datetime

    from ada.configuration.tools import (
        ToolConfigurationBundle,
        ToolConfigurationProjection,
        build_tool_manifest,
        integrated_operations_configuration_from_manifest,
    )
    from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST

    configuration = integrated_operations_configuration_from_manifest(
        INTEGRATED_OPERATIONS_MANIFEST
    )
    bundle = ToolConfigurationBundle.create(
        configuration=configuration,
        saved_by='tester',
        now_utc=datetime(2026, 8, 24, 12, 0, tzinfo=UTC),
    )
    projection = ToolConfigurationProjection.create(
        source_revision=bundle.revision,
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 24, 12, 1, tzinfo=UTC),
        manifest=build_tool_manifest(configuration),
    )

    bundle_document = bundle.to_document()
    projection_document = projection.to_document(item_id='tool', partition_key='tool')

    assert bundle_document['schema_version'] == 2
    assert 'configuration' in bundle_document
    assert 'catalog' not in bundle_document
    assert projection_document['schema_version'] == 3
    assert 'runtime' in projection_document
    assert 'manifest' in projection_document
    assert 'registry' not in projection_document
