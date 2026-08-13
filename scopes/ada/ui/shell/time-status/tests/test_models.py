from datetime import UTC, datetime

import pytest

from ada.contracts.tool_manifest import ToolSourceKey
from ada.runtime.web import SourceState
from ada.ui.shell.time_status import TimeStatusSourceState, TimeStatusState


def test_time_status_requires_pi_and_unique_sources() -> None:
    pi = TimeStatusSourceState(
        key=ToolSourceKey.PI,
        label='PI System',
        stale_after_seconds=300,
        runtime_state=SourceState.healthy(
            'pi',
            updated_at_utc=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
        ),
    )
    assert TimeStatusState(tool_key='integrated_operations', sources=(pi,)).sources == (pi,)

    with pytest.raises(ValueError, match='requires the pi source'):
        TimeStatusState(
            tool_key='integrated_operations',
            sources=(
                TimeStatusSourceState(
                    key=ToolSourceKey.DISPATCH,
                    label='Dispatch',
                    stale_after_seconds=600,
                    runtime_state=SourceState.unavailable('dispatch'),
                ),
            ),
        )


def test_time_status_source_rejects_runtime_key_mismatch() -> None:
    with pytest.raises(ValueError, match='does not match'):
        TimeStatusSourceState(
            key=ToolSourceKey.PI,
            label='PI System',
            stale_after_seconds=300,
            runtime_state=SourceState.unavailable('dispatch'),
        )
