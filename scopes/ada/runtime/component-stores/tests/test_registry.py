from datetime import UTC, datetime

import pytest

from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.runtime.component_stores import (
    RuntimeComponentStoreError,
    build_runtime_component_store_registry,
)


def _projection() -> ToolConfigurationProjection:
    return ToolConfigurationProjection.create(
        source_revision='source-r1',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )


def test_registry_materializes_every_tool_runtime_component_binding() -> None:
    projection = _projection()

    registry = build_runtime_component_store_registry(projection)

    assert registry.tool_key == projection.manifest.tool_key
    assert tuple(component.component_key for component in registry.components) == tuple(
        binding.component_key for binding in projection.runtime.components
    )
    assert len(registry.components) == len(projection.runtime.components)


def test_registry_uses_authoritative_runtime_binding_ids_without_rebuilding_them() -> None:
    projection = _projection()
    expected = projection.runtime.component('molienda')

    component = build_runtime_component_store_registry(projection).component('molienda')

    assert component.wrapper_id == expected.wrapper_id
    assert component.latest_store_id == expected.kpi_latest_store_id
    assert component.timeseries_store_id == expected.kpi_timeseries_store_id


def test_registry_resolves_store_ids_for_manual_ui_callbacks() -> None:
    registry = build_runtime_component_store_registry(_projection())

    assert registry.latest('molienda') == 'ada-runtime-kpi-latest-molienda'
    assert registry.timeseries('molienda') == 'ada-runtime-kpi-timeseries-molienda'


def test_registry_rejects_unknown_component() -> None:
    registry = build_runtime_component_store_registry(_projection())

    with pytest.raises(RuntimeComponentStoreError, match='Unknown runtime component'):
        registry.component('no_existe')


def test_registry_accepts_schema_two_projection_after_tools_derives_runtime_bindings() -> None:
    projection = _projection()
    document = projection.to_document(item_id='tool', partition_key='tool')
    document['schema_version'] = 2
    document.pop('runtime')
    restored = ToolConfigurationProjection.from_document(document)

    registry = build_runtime_component_store_registry(restored)

    assert (
        registry.latest('molienda') == projection.runtime.component('molienda').kpi_latest_store_id
    )
