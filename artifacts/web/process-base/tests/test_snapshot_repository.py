from ada.runtime.web import SnapshotChannel
from process_base.snapshot_repository import ProcessBaseSnapshotRepository
from process_base.tool import COMPOSITION


def test_process_base_repository_projects_all_active_dashboard_channels() -> None:
    repository = ProcessBaseSnapshotRepository(COMPOSITION.dashboard)

    data = repository.read_snapshot('process_base', SnapshotChannel.DATA)
    time_series = repository.read_snapshot('process_base', SnapshotChannel.TIME_SERIES)
    status = repository.read_snapshot('process_base', SnapshotChannel.STATUS)

    assert set(data.payload['components']) == {
        'upstream',
        'main_process',
        'downstream',
        'trends',
    }
    assert set(time_series.payload['components']) == {'main_process', 'trends'}
    trend_window = time_series.payload['components']['trends']['windows'][0]
    assert trend_window['hours'] == 24
    assert len(trend_window['series']['overview']) == 1440
    assert set(status.payload['components']) == {
        'upstream',
        'main_process',
        'downstream',
        'trends',
    }
