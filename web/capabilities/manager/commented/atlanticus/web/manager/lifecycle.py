# Centraliza la máquina de estados que separa editor, borrador, validación, verificación de Source y publicación.
# Projection queda deliberadamente fuera de este contrato porque su activación siempre es manual e independiente.

from dataclasses import dataclass

from atlanticus.web.manager.projection import ManagerDraft, SourceVerificationResult


@dataclass(frozen=True, slots=True)
class ManagerLifecycleState:
    dirty: bool
    published: bool
    validation_current: bool
    verification_current: bool
    source_conflict: bool
    can_save_draft: bool
    can_validate: bool
    can_verify_source: bool
    can_publish: bool
    can_force_publish: bool


def resolve_manager_lifecycle(
    *,
    draft: ManagerDraft | None,
    editor_revision: str | None,
    source_revision: str | None,
    validation_current: bool,
    source_verification: SourceVerificationResult | None,
) -> ManagerLifecycleState:
    normalized_editor_revision = _optional_revision(editor_revision)
    reference_revision = draft.revision if draft is not None else source_revision
    dirty = bool(
        normalized_editor_revision is not None and normalized_editor_revision != reference_revision
    )
    published = bool(draft is not None and draft.revision == source_revision)
    current_validation = bool(validation_current and not dirty and draft is not None)
    current_verification = bool(
        current_validation
        and source_verification is not None
        and source_verification.draft_revision == draft.revision
    )
    verification_matches = bool(
        current_verification and source_verification is not None and source_verification.matches
    )
    conflict = bool(current_verification and not verification_matches)
    return ManagerLifecycleState(
        dirty=dirty,
        published=published,
        validation_current=current_validation,
        verification_current=current_verification,
        source_conflict=conflict,
        can_save_draft=dirty,
        can_validate=bool(
            draft is not None and not dirty and not published and not current_validation
        ),
        can_verify_source=bool(current_validation and not published and not current_verification),
        can_publish=bool(verification_matches and not published),
        can_force_publish=bool(current_validation and conflict),
    )


def _optional_revision(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
