from __future__ import annotations

import json
import os
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from atlanticus.web.users.configuration.bundle import (
    UsersConfigurationBundle,
    UsersConfigurationSourceDocument,
    decode_users_configuration_source,
    encode_users_configuration_source,
)
from atlanticus.web.users.configuration.errors import (
    UsersConfigurationProjectionError,
    UsersConfigurationPublisherError,
    UsersConfigurationSourceError,
)
from atlanticus.web.users.configuration.projection import UsersProjectionState


@dataclass(frozen=True, slots=True)
class FileUsersConfigurationSettings:
    root: Path
    source_filename: str = 'users_configuration.json.gz'
    projection_filename: str = 'users_projection_state.json'


class FileUsersConfigurationStore:
    def __init__(self, settings: FileUsersConfigurationSettings) -> None:
        self._settings = settings

    def fetch_bundle(self) -> UsersConfigurationBundle | None:
        source = self._load_source()
        return source.current_bundle() if source is not None else None

    def publish_bundle(self, bundle: UsersConfigurationBundle) -> None:
        try:
            current = self._load_source()
            updated = (
                UsersConfigurationSourceDocument.from_bundle(bundle)
                if current is None
                else current.publish(bundle)
            )
            if current == updated:
                return
            _atomic_write_bytes(
                self._source_path,
                encode_users_configuration_source(updated),
            )
        except (UsersConfigurationPublisherError, UsersConfigurationSourceError):
            raise
        except Exception as error:
            raise UsersConfigurationPublisherError(
                'Could not publish local users configuration'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[UsersConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> UsersConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> UsersConfigurationSourceDocument | None:
        if not self._source_path.exists():
            return None
        try:
            return decode_users_configuration_source(self._source_path.read_bytes())
        except Exception as error:
            raise UsersConfigurationSourceError(
                'Local users configuration content is invalid'
            ) from error

    @property
    def _source_path(self) -> Path:
        return self._settings.root / self._settings.source_filename


class FileUsersProjectionRepository:
    def __init__(self, settings: FileUsersConfigurationSettings) -> None:
        self._settings = settings

    def load_state(self) -> UsersProjectionState | None:
        if not self._path.exists():
            return None
        try:
            document = json.loads(self._path.read_text(encoding='utf-8'))
            if not isinstance(document, dict):
                raise TypeError
            return UsersProjectionState(
                revision=str(document['revision']),
                source_revision=str(document['source_revision']),
                projected_by=str(document['projected_by']),
                projected_at_utc=datetime.fromisoformat(str(document['projected_at_utc'])),
            )
        except Exception as error:
            raise UsersConfigurationProjectionError(
                'Could not read local users projection state'
            ) from error

    def project(self, bundle: UsersConfigurationBundle, *, actor: str) -> UsersProjectionState:
        state = UsersProjectionState.create(
            source_revision=bundle.revision,
            projected_by=actor,
        )
        document = {
            'revision': state.revision,
            'source_revision': state.source_revision,
            'projected_by': state.projected_by,
            'projected_at_utc': state.projected_at_utc.isoformat(),
            'catalog': bundle.catalog.to_document(),
        }
        try:
            _atomic_write_json(self._path, document)
        except Exception as error:
            raise UsersConfigurationProjectionError(
                'Could not write local users projection'
            ) from error
        return state

    def health_check(self) -> bool:
        try:
            self._settings.root.mkdir(parents=True, exist_ok=True)
            return os.access(self._settings.root, os.R_OK | os.W_OK)
        except OSError:
            return False

    @property
    def _path(self) -> Path:
        return self._settings.root / self._settings.projection_filename


def _atomic_write_json(path: Path, document: dict[str, object]) -> None:
    payload = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    _atomic_write_bytes(path, payload)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(payload)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)
