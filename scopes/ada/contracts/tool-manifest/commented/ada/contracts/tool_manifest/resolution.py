from __future__ import annotations

from dataclasses import dataclass

from .enums import ToolManifestResolutionStatus
from .errors import ToolManifestError, ToolManifestLookupError
from .models import ToolManifest


# Separa la disponibilidad de la proyección de la validez estricta del ToolManifest.
@dataclass(frozen=True, slots=True)
class ToolManifestResolution:
    status: ToolManifestResolutionStatus
    manifest: ToolManifest | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, ToolManifestResolutionStatus):
            raise ToolManifestError(f'Invalid tool manifest resolution status: {self.status!r}')
        if self.status is ToolManifestResolutionStatus.READY:
            if self.manifest is None:
                raise ToolManifestError('Ready tool manifest resolution requires a manifest')
            return
        if self.manifest is not None:
            raise ToolManifestError(
                'Unavailable tool manifest resolution cannot include a manifest'
            )

    @property
    def ready(self) -> bool:
        return self.status is ToolManifestResolutionStatus.READY

    def require_manifest(self) -> ToolManifest:
        if self.manifest is None:
            raise ToolManifestLookupError(
                f'Tool manifest is not available: {self.status.value}'
            )
        return self.manifest

    @classmethod
    def resolved(cls, manifest: ToolManifest) -> 'ToolManifestResolution':
        return cls(ToolManifestResolutionStatus.READY, manifest)

    @classmethod
    def not_projected(cls) -> 'ToolManifestResolution':
        return cls(ToolManifestResolutionStatus.NOT_PROJECTED)

    @classmethod
    def invalid(cls) -> 'ToolManifestResolution':
        return cls(ToolManifestResolutionStatus.INVALID)

    @classmethod
    def source_error(cls) -> 'ToolManifestResolution':
        return cls(ToolManifestResolutionStatus.SOURCE_ERROR)
