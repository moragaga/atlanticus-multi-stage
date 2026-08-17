from datetime import UTC, datetime, timedelta

from dash import Dash

from ada.applications.reference.dashboard import (
    build_reference_dashboard_catalog,
    create_reference_dashboard_module,
)
from ada.applications.reference.snapshot_repository import ReferenceSnapshotRepository
from ada.features.dashboard import (
    ComponentRenderState,
    read_dashboard_channel_update,
    render_component_from_stores,
)
from ada.runtime.web import SharedSnapshotReader, SnapshotChannel
from atlanticus.web.services import ServiceRegistry


class _Clock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def test_reference_catalog_integrates_io_and_three_process_tools() -> None:
    catalog = build_reference_dashboard_catalog()

    assert tuple(catalog.dashboards) == (
        'integrated_operations',
        'process_center_right_reference',
        'process_full_reference',
        'process_full_bottom_reference',
    )
    assert len(catalog.dashboard('integrated_operations').definition.components) == 9
    assert len(catalog.dashboard('process_center_right_reference').definition.components) == 2
    assert len(catalog.dashboard('process_full_reference').definition.components) == 3
    assert len(catalog.dashboard('process_full_bottom_reference').definition.components) == 4
    assert all(
        dashboard.definition.polling is not None for dashboard in catalog.dashboards.values()
    )
    assert all(len(dashboard.mount().intervals) == 1 for dashboard in catalog.dashboards.values())


def test_reference_repository_keeps_one_revision_for_the_whole_channel_snapshot() -> None:
    catalog = build_reference_dashboard_catalog()
    clock = _Clock(datetime(2026, 8, 15, 22, 10, 3, tzinfo=UTC))
    repository = ReferenceSnapshotRepository(catalog.definitions, clock=clock)

    revision = repository.read_revision('integrated_operations', SnapshotChannel.DATA)
    snapshot = repository.read_snapshot('integrated_operations', SnapshotChannel.DATA)

    assert revision == snapshot.revision
    assert len(revision) == 20
    assert set(snapshot.payload['components']) == {
        component.section.key
        for component in catalog.dashboard('integrated_operations').definition.components
    }
    assert all('revision' not in value for value in snapshot.payload['components'].values())


def test_reference_data_polling_returns_no_update_until_global_revision_changes() -> None:
    catalog = build_reference_dashboard_catalog()
    dashboard = catalog.dashboard('integrated_operations')
    clock = _Clock(datetime(2026, 8, 15, 22, 10, 3, tzinfo=UTC))
    repository = ReferenceSnapshotRepository(catalog.definitions, clock=clock)
    reader = SharedSnapshotReader(repository, ttl_seconds=0.1, clock=lambda: 0.0)

    first = read_dashboard_channel_update(
        definition=dashboard.definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
    )
    assert first is not None

    unchanged = read_dashboard_channel_update(
        definition=dashboard.definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
        client_revision=first.revision,
    )
    assert unchanged is None

    clock.advance(12)
    reader.clear()
    changed = read_dashboard_channel_update(
        definition=dashboard.definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
        client_revision=first.revision,
    )

    assert changed is not None
    assert changed.revision != first.revision
    assert set(changed.component_values) == set(first.component_values)


def test_reference_timeseries_flows_to_component_bundle_and_renderer() -> None:
    catalog = build_reference_dashboard_catalog()
    dashboard = catalog.dashboard('integrated_operations')
    clock = _Clock(datetime(2026, 8, 15, 22, 10, 20, tzinfo=UTC))
    repository = ReferenceSnapshotRepository(catalog.definitions, clock=clock)
    reader = SharedSnapshotReader(repository)

    data = read_dashboard_channel_update(
        definition=dashboard.definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
    )
    time_series = read_dashboard_channel_update(
        definition=dashboard.definition,
        reader=reader,
        channel=SnapshotChannel.TIME_SERIES,
    )
    assert data is not None
    assert time_series is not None

    component = dashboard.definition.component('flotacion')
    result = render_component_from_stores(
        component=component,
        configuration=dashboard.definition.configuration,
        data_value=data.component_values['flotacion'],
        time_series_value=time_series.component_values['flotacion'],
    )

    assert all(state is ComponentRenderState.READY for state in result.status.states.values())
    assert result.preserve_content is False
    assert result.content is not None
    graphs = [
        item
        for content in result.content.values()
        for item in _walk(content)
        if item.__class__.__name__ == 'Graph'
    ]
    assert len(graphs) == 2


def test_reference_status_channel_is_independent_from_data_and_timeseries() -> None:
    catalog = build_reference_dashboard_catalog()
    dashboard = catalog.dashboard('process_full_bottom_reference')
    clock = _Clock(datetime(2026, 8, 15, 22, 10, 1, tzinfo=UTC))
    repository = ReferenceSnapshotRepository(catalog.definitions, clock=clock)

    data_revision = repository.read_revision(
        dashboard.definition.manifest.tool_key, SnapshotChannel.DATA
    )
    time_series_revision = repository.read_revision(
        dashboard.definition.manifest.tool_key,
        SnapshotChannel.TIME_SERIES,
    )
    status_revision = repository.read_revision(
        dashboard.definition.manifest.tool_key,
        SnapshotChannel.STATUS,
    )

    clock.advance(5)

    assert (
        repository.read_revision(
            dashboard.definition.manifest.tool_key,
            SnapshotChannel.DATA,
        )
        == data_revision
    )
    assert (
        repository.read_revision(
            dashboard.definition.manifest.tool_key,
            SnapshotChannel.TIME_SERIES,
        )
        == time_series_revision
    )
    assert (
        repository.read_revision(
            dashboard.definition.manifest.tool_key,
            SnapshotChannel.STATUS,
        )
        != status_revision
    )


def test_reference_module_registers_automatic_callbacks_for_all_tools() -> None:
    catalog = build_reference_dashboard_catalog()
    module = create_reference_dashboard_module(catalog)
    app = Dash(__name__)

    assert module.register_callbacks is not None
    module.register_callbacks(app, ServiceRegistry())

    component_count = sum(
        len(dashboard.definition.components) for dashboard in catalog.dashboards.values()
    )
    polling_count = sum(
        3 for dashboard in catalog.dashboards.values() if dashboard.definition.polling is not None
    )
    assert len(app.callback_map) == component_count * 2 + polling_count


def _walk(component):
    yield component
    props = component.to_plotly_json()['props']
    children = props.get('children')
    if children is None:
        return
    if not isinstance(children, (list, tuple)):
        children = (children,)
    for child in children:
        if hasattr(child, 'to_plotly_json'):
            yield from _walk(child)


def test_reference_e2e_keeps_static_component_cards_and_only_injects_inner_slots() -> None:
    from ada.applications.reference.integrated_operations import (
        build_reference_integrated_operations_layout,
    )

    catalog = build_reference_dashboard_catalog()
    mount = catalog.dashboard('integrated_operations').mount()
    layout = build_reference_integrated_operations_layout(mount=mount)
    nodes = tuple(_walk(layout))

    cards = [
        node
        for node in nodes
        if node.to_plotly_json()['props'].get('data-ada-component-card') == 'true'
    ]
    dashboard_content_slots = [
        node
        for node in nodes
        if isinstance(node.to_plotly_json()['props'].get('id'), str)
        and node.to_plotly_json()['props']['id'].startswith(
            'ada-dashboard--integrated_operations--'
        )
        and node.to_plotly_json()['props']['id'].endswith('--content')
    ]
    state_wrappers = [
        node
        for node in nodes
        if 'ada-state-wrapper' in str(node.to_plotly_json()['props'].get('className', ''))
    ]

    assert len(cards) == 22
    assert len(dashboard_content_slots) == 21
    assert state_wrappers == []


def test_reference_io_e2e_mounts_full_tool_view_without_rebuilding_dashboard_units() -> None:
    from ada.applications.reference.integrated_operations import (
        build_reference_integrated_operations_layout,
    )

    catalog = build_reference_dashboard_catalog()
    mount = catalog.dashboard('integrated_operations').mount()
    layout = build_reference_integrated_operations_layout(mount=mount)
    nodes = tuple(_walk(layout))
    full_view = next(
        node
        for node in nodes
        if node.to_plotly_json()['props'].get('data-ada-io-view-root') == 'integrated-operations'
    )
    body = next(
        node
        for node in nodes
        if node.to_plotly_json()['props'].get('data-ada-io-layout') == 'integrated-operations'
    )

    assert full_view.to_plotly_json()['props']['data-ada-io-view'] == 'overview'
    assert body.to_plotly_json()['props']['id'] == 'reference-integrated-operations-layout'
    assert (
        len(
            [
                node
                for node in nodes
                if node.to_plotly_json()['props'].get('data-ada-component-card') == 'true'
            ]
        )
        == 22
    )
