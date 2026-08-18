from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from ada.configuration.tools.errors import ToolConfigurationProjectionError
from ada.contracts.tool_manifest import ToolManifestRegistry

IssueLevel = Literal['error', 'warning']


@dataclass(frozen=True, slots=True)
class ToolProjectionAuditRecord:
    actor: str
    occurred_at_utc: datetime

    def __post_init__(self) -> None:
        actor = self.actor.strip()
        if not actor:
            raise ToolConfigurationProjectionError('Tool projection audit actor must not be empty')
        if self.occurred_at_utc.tzinfo is None or self.occurred_at_utc.utcoffset() is None:
            raise ToolConfigurationProjectionError(
                'Tool projection audit timestamp must be timezone-aware'
            )
        object.__setattr__(self, 'actor', actor)
        object.__setattr__(self, 'occurred_at_utc', self.occurred_at_utc.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class ToolProjectionIssue:
    code: str
    message: str
    level: IssueLevel = 'error'
    path: str | None = None

    def to_document(self) -> dict[str, object]:
        return {
            'code': self.code,
            'message': self.message,
            'level': self.level,
            'path': self.path,
        }


@dataclass(frozen=True, slots=True)
class ToolProjectionSummaryItem:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ToolConfigurationProjection:
    revision: str
    source_revision: str
    projected_by: str
    projected_at_utc: datetime
    registry: ToolManifestRegistry

    def __post_init__(self) -> None:
        revision = self.revision.strip()
        source_revision = self.source_revision.strip()
        projected_by = self.projected_by.strip()
        if not revision or not source_revision or not projected_by:
            raise ToolConfigurationProjectionError('Tool projection metadata must not be empty')
        if self.projected_at_utc.tzinfo is None or self.projected_at_utc.utcoffset() is None:
            raise ToolConfigurationProjectionError(
                'Tool projection timestamp must be timezone-aware'
            )
        occurred_at = self.projected_at_utc.astimezone(UTC)
        expected = build_tool_projection_revision(
            source_revision=source_revision,
            projected_at_utc=occurred_at,
        )
        if revision != expected:
            raise ToolConfigurationProjectionError(
                'Tool projection revision does not match metadata'
            )
        object.__setattr__(self, 'projected_at_utc', occurred_at)

    @classmethod
    def create(
        cls,
        *,
        source_revision: str,
        projected_by: str,
        projected_at_utc: datetime,
        registry: ToolManifestRegistry,
    ) -> ToolConfigurationProjection:
        occurred_at = projected_at_utc.astimezone(UTC)
        return cls(
            revision=build_tool_projection_revision(
                source_revision=source_revision,
                projected_at_utc=occurred_at,
            ),
            source_revision=source_revision,
            projected_by=projected_by,
            projected_at_utc=occurred_at,
            registry=registry,
        )

    def to_document(self, *, item_id: str, partition_key: str) -> dict[str, object]:
        return {
            'id': item_id,
            'partition_key': partition_key,
            'document_type': 'ada_tool_projection',
            'schema_version': 1,
            'revision': self.revision,
            'source_revision': self.source_revision,
            'projected_by': self.projected_by,
            'projected_at_utc': self.projected_at_utc.isoformat(),
            'registry': self.registry.to_document(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationProjection:
        if document.get('document_type') != 'ada_tool_projection':
            raise ToolConfigurationProjectionError('Tool projection document type is invalid')
        if document.get('schema_version') != 1:
            raise ToolConfigurationProjectionError('Tool projection schema version is invalid')
        try:
            registry = document['registry']
            if not isinstance(registry, dict):
                raise TypeError
            return cls(
                revision=str(document['revision']),
                source_revision=str(document['source_revision']),
                projected_by=str(document['projected_by']),
                projected_at_utc=datetime.fromisoformat(str(document['projected_at_utc'])),
                registry=ToolManifestRegistry.from_document(dict(registry)),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationProjectionError('Tool projection contract is invalid') from error


@dataclass(frozen=True, slots=True)
class ToolProjectionStatus:
    source_revision: str | None = None
    source_audit: ToolProjectionAuditRecord | None = None
    active_revision: str | None = None
    active_source_revision: str | None = None
    projection_audit: ToolProjectionAuditRecord | None = None


@dataclass(frozen=True, slots=True)
class ToolDraftValidationResult:
    draft_revision: str
    valid: bool
    audit: ToolProjectionAuditRecord
    issues: tuple[ToolProjectionIssue, ...] = ()
    summary: tuple[ToolProjectionSummaryItem, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolSourcePublicationResult:
    source_revision: str
    published: bool
    audit: ToolProjectionAuditRecord
    summary: tuple[ToolProjectionSummaryItem, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolProjectionExecutionResult:
    source_revision: str
    projection_revision: str | None
    projected: bool
    audit: ToolProjectionAuditRecord
    issues: tuple[ToolProjectionIssue, ...] = ()
    summary: tuple[ToolProjectionSummaryItem, ...] = ()


def build_tool_projection_revision(*, source_revision: str, projected_at_utc: datetime) -> str:
    payload = f'{source_revision.strip()}:{projected_at_utc.astimezone(UTC).isoformat()}'
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
