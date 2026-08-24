from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from ada.runtime.web import SnapshotChannel
from integrated_operations.runtime.snapshots import IntegratedOperationsSnapshotRepository
from integrated_operations.tool import build_integrated_operations_composition


def _composition():
    return build_integrated_operations_composition(INTEGRATED_OPERATIONS_MANIFEST)


def test_fake_repository_projects_all_dashboard_components() -> None:
    composition = _composition()
    repository = IntegratedOperationsSnapshotRepository(composition.dashboard)
    snapshot = repository.read_snapshot('integrated_operations', SnapshotChannel.DATA)

    assert set(snapshot.payload['components']) == {
        component.section.key
        for component in composition.dashboard.components
        if component.projection is not None and component.projection.data
    }


def test_fake_repository_projects_status_at_renderable_card_granularity() -> None:
    composition = _composition()
    repository = IntegratedOperationsSnapshotRepository(composition.dashboard)
    snapshot = repository.read_snapshot('integrated_operations', SnapshotChannel.STATUS)

    assert 'flotacion' in snapshot.payload['components']
    assert set(snapshot.payload['components']['flotacion']) == {'colectiva', 'selectiva'}
