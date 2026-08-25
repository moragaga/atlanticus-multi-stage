from datetime import UTC, datetime

from dash import dcc, html

from ada.configuration.tools import ToolConfigurationProjection
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.runtime.component_stores import (
    build_runtime_component_store_mount,
    build_runtime_component_store_registry,
)


def _mount():
    projection = ToolConfigurationProjection.create(
        source_revision='source-r1',
        projected_by='tester',
        projected_at_utc=datetime(2026, 8, 25, 12, 0, tzinfo=UTC),
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
    )
    registry = build_runtime_component_store_registry(projection)
    return build_runtime_component_store_mount(registry)


def test_mount_creates_exactly_two_memory_stores_per_component() -> None:
    mount = _mount()

    assert len(mount.stores) == len(mount.registry.components) * 2
    assert all(isinstance(store, dcc.Store) for store in mount.stores)
    assert all(store.storage_type == 'memory' for store in mount.stores)


def test_mount_uses_string_ids_from_tool_projection_without_pattern_matching() -> None:
    mount = _mount()
    ids = tuple(store.id for store in mount.stores)

    assert all(isinstance(store_id, str) for store_id in ids)
    assert mount.registry.latest('molienda') in ids
    assert mount.registry.timeseries('molienda') in ids


def test_mount_initializes_latest_and_timeseries_with_explicit_unmapped_shapes() -> None:
    mount = _mount()
    stores = {store.id: store for store in mount.stores}

    assert stores[mount.registry.latest('molienda')].data == {
        'state': 'unmapped',
        'items': {},
    }
    assert stores[mount.registry.timeseries('molienda')].data == {
        'state': 'unmapped',
        'windows': [],
    }


def test_runtime_host_contains_only_hidden_runtime_stores() -> None:
    mount = _mount()

    host = mount.runtime_host()

    assert isinstance(host, html.Div)
    assert host.style == {'display': 'none'}
    assert tuple(host.children) == mount.stores
