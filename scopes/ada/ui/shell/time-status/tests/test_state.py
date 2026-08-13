from dataclasses import replace
from datetime import UTC, datetime

from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST, ToolSourceKey
from ada.runtime.web import RuntimeSnapshot, SourceState
from ada.ui.shell.time_status import create_time_status_state


def test_time_status_state_follows_manifest_source_order_and_thresholds() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    snapshot = RuntimeSnapshot(
        revision='r1',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
    )

    state = create_time_status_state(
        manifest=INTEGRATED_OPERATIONS_MANIFEST,
        snapshot=snapshot,
    )

    assert [source.key for source in state.sources] == [
        ToolSourceKey.PI,
        ToolSourceKey.DISPATCH,
    ]
    assert [source.stale_after_seconds for source in state.sources] == [300, 600]


def test_time_status_omits_dispatch_when_manifest_does_not_declare_it() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    manifest = replace(
        INTEGRATED_OPERATIONS_MANIFEST,
        sources=(INTEGRATED_OPERATIONS_MANIFEST.source(ToolSourceKey.PI),),
    )
    snapshot = RuntimeSnapshot(
        revision='r2',
        loaded_at_utc=now,
        sources={
            'pi': SourceState.healthy('pi', updated_at_utc=now),
            'dispatch': SourceState.healthy('dispatch', updated_at_utc=now),
        },
    )

    state = create_time_status_state(manifest=manifest, snapshot=snapshot)

    assert [source.key for source in state.sources] == [ToolSourceKey.PI]
