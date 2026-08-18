from datetime import UTC, datetime

from atlanticus.web.manager import (
    ManagerDraft,
    ProjectionAuditRecord,
    ProjectionState,
    ProjectionStatus,
    build_draft_revision,
    resolve_projection_state,
)

_AUDIT = ProjectionAuditRecord('Admin', datetime(2026, 8, 18, 12, 0, tzinfo=UTC))


def test_projection_state_is_no_source_without_published_configuration() -> None:
    assert resolve_projection_state(ProjectionStatus()) is ProjectionState.NO_SOURCE


def test_projection_state_is_ready_when_source_is_not_active() -> None:
    status = ProjectionStatus(source_revision='source-b', source_audit=_AUDIT)

    assert resolve_projection_state(status) is ProjectionState.READY


def test_projection_state_is_synchronized_when_active_source_matches() -> None:
    status = ProjectionStatus(
        source_revision='source-a',
        source_audit=_AUDIT,
        active_revision='projection-a',
        active_source_revision='source-a',
        projection_audit=_AUDIT,
    )

    assert resolve_projection_state(status) is ProjectionState.SYNCHRONIZED


def test_manager_draft_roundtrips_browser_contract_and_base_revision() -> None:
    payload = {'tools': [{'key': 'flotacion'}]}
    draft = ManagerDraft.create(
        owner_subject_id='user-1',
        payload=payload,
        base_source_revision='source-a',
        saved_at=datetime(2026, 8, 18, 12, 10, tzinfo=UTC),
    )

    restored = ManagerDraft.from_document(draft.to_document())

    assert restored == draft
    assert restored.revision == build_draft_revision(payload)
    assert restored.base_source_revision == 'source-a'
    assert restored.with_base_source_revision('source-b').base_source_revision == 'source-b'
