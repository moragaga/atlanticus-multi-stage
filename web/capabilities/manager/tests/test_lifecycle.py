from datetime import UTC, datetime

from atlanticus.web.manager.lifecycle import resolve_manager_lifecycle
from atlanticus.web.manager.projection import (
    ManagerDraft,
    ProjectionAuditRecord,
    SourceVerificationResult,
)


def _draft() -> ManagerDraft:
    return ManagerDraft.create(
        owner_subject_id='user-1',
        payload={'value': 1},
        base_source_revision='source-a',
        saved_at=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )


def _verification(draft: ManagerDraft, source_revision: str) -> SourceVerificationResult:
    return SourceVerificationResult(
        draft_revision=draft.revision,
        base_source_revision=draft.base_source_revision,
        source_revision=source_revision,
        source_audit=ProjectionAuditRecord(
            actor='Admin',
            occurred_at=datetime(2026, 8, 21, 12, 5, tzinfo=UTC),
        ),
        checked_at=datetime(2026, 8, 21, 12, 6, tzinfo=UTC),
    )


def test_dirty_editor_only_allows_saving_draft() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision='editor-new',
        source_revision='source-a',
        validation_current=True,
        source_verification=_verification(draft, 'source-a'),
    )

    assert state.can_save_draft is True
    assert state.can_validate is False
    assert state.can_verify_source is False
    assert state.can_publish is False
    assert state.can_force_publish is False


def test_saved_draft_only_allows_validation() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision=draft.revision,
        source_revision='source-a',
        validation_current=False,
        source_verification=None,
    )

    assert state.can_save_draft is False
    assert state.can_validate is True
    assert state.can_verify_source is False
    assert state.can_publish is False


def test_valid_draft_only_allows_source_verification() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision=draft.revision,
        source_revision='source-a',
        validation_current=True,
        source_verification=None,
    )

    assert state.can_validate is False
    assert state.can_verify_source is True
    assert state.can_publish is False


def test_matching_source_verification_only_allows_publication() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision=draft.revision,
        source_revision='source-a',
        validation_current=True,
        source_verification=_verification(draft, 'source-a'),
    )

    assert state.can_verify_source is False
    assert state.can_publish is True
    assert state.source_conflict is False


def test_source_conflict_blocks_normal_publication_and_enables_force_candidate() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision=draft.revision,
        source_revision='source-b',
        validation_current=True,
        source_verification=_verification(draft, 'source-b'),
    )

    assert state.source_conflict is True
    assert state.can_publish is False
    assert state.can_force_publish is True


def test_published_draft_has_no_draft_lifecycle_action() -> None:
    draft = _draft()

    state = resolve_manager_lifecycle(
        draft=draft,
        editor_revision=draft.revision,
        source_revision=draft.revision,
        validation_current=True,
        source_verification=None,
    )

    assert state.published is True
    assert state.can_save_draft is False
    assert state.can_validate is False
    assert state.can_verify_source is False
    assert state.can_publish is False
