from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
    ToolTarget,
    build_process_manifest,
)
from ada.features.dashboard import (
    ComponentProjectionDefinition,
    ComponentRendererDefinition,
    ComponentRendererRegistry,
    DashboardDefinition,
    DashboardPollingSettings,
    DashboardToolConfiguration,
    TimeSeriesProjectionDefinition,
    TimeSeriesSettings,
    dashboard_snapshot_channels,
    read_dashboard_channel_update,
)
from ada.runtime.web import SharedSnapshot, SharedSnapshotReader, SnapshotChannel


class Repository:
    def __init__(self) -> None:
        self.revisions = {
            SnapshotChannel.DATA: '20260815210000100000',
            SnapshotChannel.TIME_SERIES: '20260815210000200000',
            SnapshotChannel.STATUS: '20260815210000300000',
        }
        self.snapshots = {
            SnapshotChannel.DATA: SharedSnapshot(
                revision=self.revisions[SnapshotChannel.DATA],
                payload={
                    'components': {
                        'center_process': {'kpi': 87},
                        'right_process': {'kpi': 42},
                    }
                },
            ),
            SnapshotChannel.TIME_SERIES: SharedSnapshot(
                revision=self.revisions[SnapshotChannel.TIME_SERIES],
                payload={
                    'components': {
                        'center_process': {
                            'windows': [
                                {
                                    'hours': 1,
                                    'start_utc': '2026-08-15T20:00:00Z',
                                    'end_utc': '2026-08-15T21:00:00Z',
                                    'series': {'ley': [1, 2, 3, 4, 5, 6]},
                                }
                            ]
                        }
                    }
                },
            ),
            SnapshotChannel.STATUS: SharedSnapshot(
                revision=self.revisions[SnapshotChannel.STATUS],
                payload={
                    'components': {
                        'center_process': {'main': 'ready'},
                        'right_process': {'main': 'stale'},
                    }
                },
            ),
        }
        self.revision_reads = 0
        self.snapshot_reads = 0

    def read_revision(self, _tool_key, channel):
        self.revision_reads += 1
        return self.revisions[channel]

    def read_snapshot(self, _tool_key, channel):
        self.snapshot_reads += 1
        return self.snapshots[channel]


def _definition() -> DashboardDefinition:
    manifest = build_process_manifest(
        tool_key='polling_reference',
        display_name='Polling Reference',
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=60),),
        operational_scope=ToolScope.PLANT,
        body_sections=(
            ToolSection(
                key='center_process',
                display_name='Centro',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI, ToolTarget.ALARM),
                layout_role=ProcessBodySection.CENTER,
            ),
            ToolSection(
                component='center_process',
                subcomponent='main',
                display_name='Principal',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
                targets=(ToolTarget.ALARM,),
            ),
            ToolSection(
                key='right_process',
                display_name='Derecha',
                kind=ToolSectionKind.COMPONENT,
                scope=ToolScope.PLANT,
                parent_key='body',
                targets=(ToolTarget.KPI,),
                layout_role=ProcessBodySection.RIGHT,
            ),
            ToolSection(
                component='right_process',
                subcomponent='main',
                display_name='Principal',
                kind=ToolSectionKind.SUBCOMPONENT,
                scope=ToolScope.PLANT,
            ),
        ),
    )
    return DashboardDefinition.build(
        manifest=manifest,
        configuration=DashboardToolConfiguration(
            components=(
                ComponentProjectionDefinition(
                    component_key='center_process',
                    data=True,
                    time_series=(TimeSeriesProjectionDefinition(key='ley', hours=1),),
                ),
                ComponentProjectionDefinition(component_key='right_process', data=True),
            ),
            time_series=TimeSeriesSettings(step_seconds=600, display_timezone='America/Santiago'),
        ),
        renderers=ComponentRendererRegistry(
            definitions=(
                ComponentRendererDefinition(
                    component_key='center_process',
                    renderer=lambda bundle: {'main': bundle.component_key},
                ),
                ComponentRendererDefinition(
                    component_key='right_process',
                    renderer=lambda bundle: {'main': bundle.component_key},
                ),
            )
        ),
        polling=DashboardPollingSettings(interval_seconds=5),
    )


def test_polling_channels_are_derived_from_active_dashboard_contract() -> None:
    assert dashboard_snapshot_channels(_definition()) == (
        SnapshotChannel.DATA,
        SnapshotChannel.TIME_SERIES,
        SnapshotChannel.STATUS,
    )


def test_channel_poll_reads_one_global_revision_and_distributes_whole_snapshot() -> None:
    repository = Repository()
    reader = SharedSnapshotReader(repository, ttl_seconds=1)

    update = read_dashboard_channel_update(
        definition=_definition(),
        reader=reader,
        channel=SnapshotChannel.DATA,
    )

    assert update is not None
    assert update.revision == '20260815210000100000'
    assert tuple(update.component_values) == ('center_process', 'right_process')
    assert repository.revision_reads == 1
    assert repository.snapshot_reads == 1


def test_same_global_revision_returns_no_update_without_component_revisions() -> None:
    repository = Repository()
    reader = SharedSnapshotReader(repository, ttl_seconds=1)
    definition = _definition()

    first = read_dashboard_channel_update(
        definition=definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
    )
    second = read_dashboard_channel_update(
        definition=definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
        client_revision=first.revision,
    )

    assert second is None
    assert repository.revision_reads == 1
    assert repository.snapshot_reads == 1


def test_new_global_revision_redistributes_all_declared_component_stores() -> None:
    repository = Repository()
    reader = SharedSnapshotReader(repository, ttl_seconds=0.001)
    definition = _definition()
    first = read_dashboard_channel_update(
        definition=definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
    )
    repository.revisions[SnapshotChannel.DATA] = '20260815210001100000'
    repository.snapshots[SnapshotChannel.DATA] = SharedSnapshot(
        revision='20260815210001100000',
        payload={
            'components': {
                'center_process': {'kpi': 88},
                'right_process': {'kpi': 42},
            }
        },
    )
    reader.clear()

    update = read_dashboard_channel_update(
        definition=definition,
        reader=reader,
        channel=SnapshotChannel.DATA,
        client_revision=first.revision,
    )

    assert update is not None
    assert update.revision == '20260815210001100000'
    assert set(update.component_values) == {'center_process', 'right_process'}
    assert 'revision' not in update.component_values['center_process']
    assert 'revision' not in update.component_values['right_process']


def test_status_is_independent_from_data_and_time_series_revisions() -> None:
    repository = Repository()
    reader = SharedSnapshotReader(repository, ttl_seconds=1)

    update = read_dashboard_channel_update(
        definition=_definition(),
        reader=reader,
        channel=SnapshotChannel.STATUS,
    )

    assert update is not None
    assert update.revision == repository.revisions[SnapshotChannel.STATUS]
    assert update.component_values['center_process']['states'] == {'main': 'ready'}
    assert update.component_values['right_process']['states'] == {'main': 'stale'}
