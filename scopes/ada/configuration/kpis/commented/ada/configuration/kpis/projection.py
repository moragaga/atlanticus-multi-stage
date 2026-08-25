# Define la proyección KPI estable y registra la revisión exacta de Tool Projection utilizada.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from ada.configuration.kpis.errors import KpiConfigurationProjectionError
from ada.configuration.kpis.models import KpiConfiguration

IssueLevel = Literal['error', 'warning']


@dataclass(frozen=True, slots=True)
class KpiProjectionAuditRecord:
    actor: str
    occurred_at_utc: datetime

    def __post_init__(self) -> None:
        actor = self.actor.strip()
        if not actor:
            raise KpiConfigurationProjectionError('KPI projection audit actor must not be empty')
        if self.occurred_at_utc.tzinfo is None or self.occurred_at_utc.utcoffset() is None:
            raise KpiConfigurationProjectionError(
                'KPI projection audit timestamp must be timezone-aware'
            )
        object.__setattr__(self, 'actor', actor)
        object.__setattr__(self, 'occurred_at_utc', self.occurred_at_utc.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class KpiProjectionIssue:
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
class KpiProjectionSummaryItem:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class KpiConfigurationProjection:
    revision: str
    source_revision: str
    tool_projection_revision: str
    projected_by: str
    projected_at_utc: datetime
    configuration: KpiConfiguration

    def __post_init__(self) -> None:
        revision = self.revision.strip()
        source_revision = self.source_revision.strip()
        tool_projection_revision = self.tool_projection_revision.strip()
        projected_by = self.projected_by.strip()
        if not revision or not source_revision or not tool_projection_revision or not projected_by:
            raise KpiConfigurationProjectionError('KPI projection metadata must not be empty')
        if self.projected_at_utc.tzinfo is None or self.projected_at_utc.utcoffset() is None:
            raise KpiConfigurationProjectionError('KPI projection timestamp must be timezone-aware')
        occurred_at = self.projected_at_utc.astimezone(UTC)
        expected = build_kpi_projection_revision(
            source_revision=source_revision,
            tool_projection_revision=tool_projection_revision,
            projected_at_utc=occurred_at,
        )
        if revision != expected:
            raise KpiConfigurationProjectionError('KPI projection revision does not match metadata')
        if not isinstance(self.configuration, KpiConfiguration):
            raise KpiConfigurationProjectionError('KPI projection configuration is invalid')
        object.__setattr__(self, 'projected_at_utc', occurred_at)

    @classmethod
    def create(
        cls,
        *,
        source_revision: str,
        tool_projection_revision: str,
        projected_by: str,
        projected_at_utc: datetime,
        configuration: KpiConfiguration,
    ) -> KpiConfigurationProjection:
        occurred_at = projected_at_utc.astimezone(UTC)
        return cls(
            revision=build_kpi_projection_revision(
                source_revision=source_revision,
                tool_projection_revision=tool_projection_revision,
                projected_at_utc=occurred_at,
            ),
            source_revision=source_revision,
            tool_projection_revision=tool_projection_revision,
            projected_by=projected_by,
            projected_at_utc=occurred_at,
            configuration=configuration,
        )

    def to_document(self, *, item_id: str, partition_key: str) -> dict[str, object]:
        return {
            'id': item_id,
            'partition_key': partition_key,
            'document_type': 'ada_kpi_configuration_projection',
            'schema_version': 1,
            'revision': self.revision,
            'source_revision': self.source_revision,
            'tool_projection_revision': self.tool_projection_revision,
            'projected_by': self.projected_by,
            'projected_at_utc': self.projected_at_utc.isoformat(),
            'configuration': self.configuration.to_document(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> KpiConfigurationProjection:
        if document.get('document_type') != 'ada_kpi_configuration_projection':
            raise KpiConfigurationProjectionError('KPI projection document type is invalid')
        if document.get('schema_version') != 1:
            raise KpiConfigurationProjectionError('KPI projection schema version is invalid')
        try:
            configuration = document['configuration']
            if not isinstance(configuration, dict):
                raise TypeError
            return cls(
                revision=str(document['revision']),
                source_revision=str(document['source_revision']),
                tool_projection_revision=str(document['tool_projection_revision']),
                projected_by=str(document['projected_by']),
                projected_at_utc=datetime.fromisoformat(str(document['projected_at_utc'])),
                configuration=KpiConfiguration.from_document(dict(configuration)),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise KpiConfigurationProjectionError('KPI projection contract is invalid') from error


@dataclass(frozen=True, slots=True)
class KpiProjectionStatus:
    source_revision: str | None = None
    source_audit: KpiProjectionAuditRecord | None = None
    active_revision: str | None = None
    active_source_revision: str | None = None
    active_tool_projection_revision: str | None = None
    projection_audit: KpiProjectionAuditRecord | None = None


@dataclass(frozen=True, slots=True)
class KpiDraftValidationResult:
    draft_revision: str
    valid: bool
    audit: KpiProjectionAuditRecord
    tool_projection_revision: str | None = None
    issues: tuple[KpiProjectionIssue, ...] = ()
    summary: tuple[KpiProjectionSummaryItem, ...] = ()


@dataclass(frozen=True, slots=True)
class KpiSourcePublicationResult:
    source_revision: str
    published: bool
    audit: KpiProjectionAuditRecord
    tool_projection_revision: str | None = None
    summary: tuple[KpiProjectionSummaryItem, ...] = ()


@dataclass(frozen=True, slots=True)
class KpiProjectionExecutionResult:
    source_revision: str
    projection_revision: str | None
    tool_projection_revision: str
    projected: bool
    audit: KpiProjectionAuditRecord
    issues: tuple[KpiProjectionIssue, ...] = ()
    summary: tuple[KpiProjectionSummaryItem, ...] = ()


def build_kpi_projection_revision(
    *,
    source_revision: str,
    tool_projection_revision: str,
    projected_at_utc: datetime,
) -> str:
    payload = ':'.join(
        (
            source_revision.strip(),
            tool_projection_revision.strip(),
            projected_at_utc.astimezone(UTC).isoformat(),
        )
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
