from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from ada.configuration.tools.errors import ToolConfigurationValidationError
from ada.configuration.tools.models import ToolConfigurationCatalog

BUNDLE_DOCUMENT_TYPE = 'ada_tool_configuration'
SOURCE_DOCUMENT_TYPE = 'ada_tool_configuration_source'
SCHEMA_VERSION = 1
DEFAULT_MAX_COMPRESSED_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_DECOMPRESSED_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ToolConfigurationBundle:
    catalog: ToolConfigurationCatalog
    revision: str
    saved_by: str
    saved_at_utc: datetime

    def __post_init__(self) -> None:
        revision = build_tool_configuration_digest(self.catalog)
        saved_by = self.saved_by.strip()
        if self.revision.strip() != revision:
            raise ToolConfigurationValidationError(
                'Tool configuration source revision does not match content'
            )
        if not saved_by:
            raise ToolConfigurationValidationError(
                'Tool configuration source audit actor must not be empty'
            )
        if self.saved_at_utc.tzinfo is None or self.saved_at_utc.utcoffset() is None:
            raise ToolConfigurationValidationError(
                'Tool configuration source audit timestamp must be timezone-aware'
            )
        object.__setattr__(self, 'revision', revision)
        object.__setattr__(self, 'saved_by', saved_by)
        object.__setattr__(self, 'saved_at_utc', self.saved_at_utc.astimezone(UTC))

    @classmethod
    def create(
        cls,
        *,
        catalog: ToolConfigurationCatalog,
        saved_by: str,
        now_utc: datetime | None = None,
    ) -> ToolConfigurationBundle:
        return cls(
            catalog=catalog,
            revision=build_tool_configuration_digest(catalog),
            saved_by=saved_by,
            saved_at_utc=(now_utc or datetime.now(UTC)).astimezone(UTC),
        )

    def to_document(self) -> dict[str, object]:
        return {
            'document_type': BUNDLE_DOCUMENT_TYPE,
            'schema_version': SCHEMA_VERSION,
            'revision': self.revision,
            'saved_by': self.saved_by,
            'saved_at_utc': self.saved_at_utc.isoformat(),
            'catalog': self.catalog.to_document(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationBundle:
        if document.get('document_type') != BUNDLE_DOCUMENT_TYPE:
            raise ToolConfigurationValidationError(
                'Tool configuration document type is invalid'
            )
        if document.get('schema_version') != SCHEMA_VERSION:
            raise ToolConfigurationValidationError(
                'Tool configuration schema version is invalid'
            )
        try:
            catalog = document['catalog']
            if not isinstance(catalog, dict):
                raise TypeError
            return cls(
                catalog=ToolConfigurationCatalog.from_document(dict(catalog)),
                revision=str(document['revision']),
                saved_by=str(document['saved_by']),
                saved_at_utc=datetime.fromisoformat(str(document['saved_at_utc'])),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool configuration contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolConfigurationVersion:
    catalog: ToolConfigurationCatalog
    revision: str
    created_by: str
    created_at_utc: datetime

    def __post_init__(self) -> None:
        expected = build_tool_configuration_digest(self.catalog)
        actor = self.created_by.strip()
        if self.revision.strip() != expected:
            raise ToolConfigurationValidationError(
                'Tool configuration version revision does not match content'
            )
        if not actor:
            raise ToolConfigurationValidationError(
                'Tool configuration version actor must not be empty'
            )
        if self.created_at_utc.tzinfo is None or self.created_at_utc.utcoffset() is None:
            raise ToolConfigurationValidationError(
                'Tool configuration version timestamp must be timezone-aware'
            )
        object.__setattr__(self, 'revision', expected)
        object.__setattr__(self, 'created_by', actor)
        object.__setattr__(self, 'created_at_utc', self.created_at_utc.astimezone(UTC))

    @classmethod
    def from_bundle(cls, bundle: ToolConfigurationBundle) -> ToolConfigurationVersion:
        return cls(
            catalog=bundle.catalog,
            revision=bundle.revision,
            created_by=bundle.saved_by,
            created_at_utc=bundle.saved_at_utc,
        )

    def to_document(self) -> dict[str, object]:
        return {
            'revision': self.revision,
            'created_by': self.created_by,
            'created_at_utc': self.created_at_utc.isoformat(),
            'catalog': self.catalog.to_document(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationVersion:
        try:
            catalog = document['catalog']
            if not isinstance(catalog, dict):
                raise TypeError
            return cls(
                catalog=ToolConfigurationCatalog.from_document(dict(catalog)),
                revision=str(document['revision']),
                created_by=str(document['created_by']),
                created_at_utc=datetime.fromisoformat(str(document['created_at_utc'])),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool configuration version contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolConfigurationPublication:
    revision: str
    published_by: str
    published_at_utc: datetime

    def __post_init__(self) -> None:
        revision = self.revision.strip()
        actor = self.published_by.strip()
        if not revision or not actor:
            raise ToolConfigurationValidationError(
                'Tool configuration publication metadata must not be empty'
            )
        if self.published_at_utc.tzinfo is None or self.published_at_utc.utcoffset() is None:
            raise ToolConfigurationValidationError(
                'Tool configuration publication timestamp must be timezone-aware'
            )
        object.__setattr__(self, 'revision', revision)
        object.__setattr__(self, 'published_by', actor)
        object.__setattr__(self, 'published_at_utc', self.published_at_utc.astimezone(UTC))

    def to_document(self) -> dict[str, object]:
        return {
            'revision': self.revision,
            'published_by': self.published_by,
            'published_at_utc': self.published_at_utc.isoformat(),
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationPublication:
        try:
            return cls(
                revision=str(document['revision']),
                published_by=str(document['published_by']),
                published_at_utc=datetime.fromisoformat(
                    str(document['published_at_utc'])
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool configuration publication contract is invalid'
            ) from error


@dataclass(frozen=True, slots=True)
class ToolConfigurationSourceDocument:
    current_revision: str
    versions: tuple[ToolConfigurationVersion, ...]
    publications: tuple[ToolConfigurationPublication, ...]

    def __post_init__(self) -> None:
        current = self.current_revision.strip()
        versions = tuple(self.versions)
        publications = tuple(self.publications)
        version_keys = tuple(version.revision for version in versions)
        if not current:
            raise ToolConfigurationValidationError(
                'Tool configuration current revision must not be empty'
            )
        if len(version_keys) != len(set(version_keys)):
            raise ToolConfigurationValidationError(
                'Tool configuration versions must be unique by revision'
            )
        if current not in version_keys:
            raise ToolConfigurationValidationError(
                'Tool configuration current revision does not exist in versions'
            )
        if not publications or publications[-1].revision != current:
            raise ToolConfigurationValidationError(
                'Tool configuration current publication metadata is invalid'
            )
        if any(publication.revision not in version_keys for publication in publications):
            raise ToolConfigurationValidationError(
                'Tool configuration publication references an unknown revision'
            )
        object.__setattr__(self, 'current_revision', current)
        object.__setattr__(self, 'versions', versions)
        object.__setattr__(self, 'publications', publications)

    @classmethod
    def from_bundle(cls, bundle: ToolConfigurationBundle) -> ToolConfigurationSourceDocument:
        return cls(
            current_revision=bundle.revision,
            versions=(ToolConfigurationVersion.from_bundle(bundle),),
            publications=(
                ToolConfigurationPublication(
                    revision=bundle.revision,
                    published_by=bundle.saved_by,
                    published_at_utc=bundle.saved_at_utc,
                ),
            ),
        )

    def publish(self, bundle: ToolConfigurationBundle) -> ToolConfigurationSourceDocument:
        if self.current_revision == bundle.revision:
            return self
        versions = list(self.versions)
        if not any(version.revision == bundle.revision for version in versions):
            versions.append(ToolConfigurationVersion.from_bundle(bundle))
        publications = self.publications + (
            ToolConfigurationPublication(
                revision=bundle.revision,
                published_by=bundle.saved_by,
                published_at_utc=bundle.saved_at_utc,
            ),
        )
        return ToolConfigurationSourceDocument(
            current_revision=bundle.revision,
            versions=tuple(versions),
            publications=publications,
        )

    def current_bundle(self) -> ToolConfigurationBundle:
        return self._bundle_for_revision(self.current_revision)

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]:
        if limit < 1:
            return ()
        latest_publication: dict[str, ToolConfigurationPublication] = {}
        for publication in self.publications:
            latest_publication[publication.revision] = publication
        ordered = sorted(
            self.versions,
            key=lambda version: latest_publication[version.revision].published_at_utc,
            reverse=True,
        )
        return tuple(
            self._bundle_for_revision(version.revision)
            for version in ordered[:limit]
        )

    def fetch_revision(self, revision: str) -> ToolConfigurationBundle | None:
        normalized = revision.strip()
        if not any(version.revision == normalized for version in self.versions):
            return None
        return self._bundle_for_revision(normalized)

    def to_document(self) -> dict[str, object]:
        return {
            'document_type': SOURCE_DOCUMENT_TYPE,
            'schema_version': SCHEMA_VERSION,
            'current_revision': self.current_revision,
            'versions': [version.to_document() for version in self.versions],
            'publications': [publication.to_document() for publication in self.publications],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> ToolConfigurationSourceDocument:
        if document.get('document_type') != SOURCE_DOCUMENT_TYPE:
            raise ToolConfigurationValidationError(
                'Tool configuration source document type is invalid'
            )
        if document.get('schema_version') != SCHEMA_VERSION:
            raise ToolConfigurationValidationError(
                'Tool configuration source schema version is invalid'
            )
        try:
            versions = document['versions']
            publications = document['publications']
            if not isinstance(versions, list) or not all(
                isinstance(item, dict) for item in versions
            ):
                raise TypeError
            if not isinstance(publications, list) or not all(
                isinstance(item, dict) for item in publications
            ):
                raise TypeError
            return cls(
                current_revision=str(document['current_revision']),
                versions=tuple(
                    ToolConfigurationVersion.from_document(dict(item)) for item in versions
                ),
                publications=tuple(
                    ToolConfigurationPublication.from_document(dict(item))
                    for item in publications
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ToolConfigurationValidationError(
                'Tool configuration source contract is invalid'
            ) from error

    def _bundle_for_revision(self, revision: str) -> ToolConfigurationBundle:
        version = next(item for item in self.versions if item.revision == revision)
        publication = next(
            item for item in reversed(self.publications) if item.revision == revision
        )
        return ToolConfigurationBundle(
            catalog=version.catalog,
            revision=version.revision,
            saved_by=publication.published_by,
            saved_at_utc=publication.published_at_utc,
        )


def build_tool_configuration_digest(catalog: ToolConfigurationCatalog) -> str:
    canonical = json.dumps(
        catalog.to_document(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def encode_tool_configuration_bundle(bundle: ToolConfigurationBundle) -> bytes:
    return _encode_document(bundle.to_document())


def decode_tool_configuration_bundle(
    payload: bytes,
    *,
    max_compressed_bytes: int = DEFAULT_MAX_COMPRESSED_BYTES,
    max_decompressed_bytes: int = DEFAULT_MAX_DECOMPRESSED_BYTES,
) -> ToolConfigurationBundle:
    document = _decode_document(
        payload,
        max_compressed_bytes=max_compressed_bytes,
        max_decompressed_bytes=max_decompressed_bytes,
    )
    return ToolConfigurationBundle.from_document(document)


def encode_tool_configuration_source(source: ToolConfigurationSourceDocument) -> bytes:
    return _encode_document(source.to_document())


def decode_tool_configuration_source(
    payload: bytes,
    *,
    max_compressed_bytes: int = DEFAULT_MAX_COMPRESSED_BYTES,
    max_decompressed_bytes: int = DEFAULT_MAX_DECOMPRESSED_BYTES,
) -> ToolConfigurationSourceDocument:
    document = _decode_document(
        payload,
        max_compressed_bytes=max_compressed_bytes,
        max_decompressed_bytes=max_decompressed_bytes,
    )
    return ToolConfigurationSourceDocument.from_document(document)


def decode_tool_configuration_import(payload: bytes) -> ToolConfigurationCatalog:
    document = _decode_document(
        payload,
        max_compressed_bytes=DEFAULT_MAX_COMPRESSED_BYTES,
        max_decompressed_bytes=DEFAULT_MAX_DECOMPRESSED_BYTES,
    )
    document_type = document.get('document_type')
    if document_type == SOURCE_DOCUMENT_TYPE:
        return ToolConfigurationSourceDocument.from_document(document).current_bundle().catalog
    if document_type == BUNDLE_DOCUMENT_TYPE:
        return ToolConfigurationBundle.from_document(document).catalog
    raise ToolConfigurationValidationError('Tool configuration import document type is invalid')


def _encode_document(document: dict[str, object]) -> bytes:
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return gzip.compress(canonical, compresslevel=9, mtime=0)


def _decode_document(
    payload: bytes,
    *,
    max_compressed_bytes: int,
    max_decompressed_bytes: int,
) -> dict[str, Any]:
    if not payload:
        raise ToolConfigurationValidationError('Tool configuration file must not be empty')
    if len(payload) > max_compressed_bytes:
        raise ToolConfigurationValidationError('Tool configuration file exceeds the size limit')
    if payload[:2] != b'\x1f\x8b':
        raise ToolConfigurationValidationError('Tool configuration file must be gzip encoded')
    try:
        with gzip.GzipFile(fileobj=BytesIO(payload), mode='rb') as compressed:
            decoded = compressed.read(max_decompressed_bytes + 1)
    except (OSError, EOFError) as error:
        raise ToolConfigurationValidationError(
            'Tool configuration gzip content is invalid'
        ) from error
    if len(decoded) > max_decompressed_bytes:
        raise ToolConfigurationValidationError(
            'Tool configuration decompressed content exceeds the size limit'
        )
    try:
        document = json.loads(decoded.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolConfigurationValidationError(
            'Tool configuration must contain valid UTF-8 JSON'
        ) from error
    if not isinstance(document, dict):
        raise ToolConfigurationValidationError('Tool configuration root must be an object')
    return document
