# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Simula Source y Projection en archivos separados para pruebas locales.
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from ada.configuration.tools.bundle import (
    ToolConfigurationBundle,
    ToolConfigurationSourceDocument,
    decode_tool_configuration_source,
    encode_tool_configuration_source,
)
from ada.configuration.tools.errors import (
    ToolConfigurationProjectionError,
    ToolConfigurationPublisherError,
    ToolConfigurationSourceError,
)
from ada.configuration.tools.projection import ToolConfigurationProjection


@dataclass(frozen=True, slots=True)
class FileToolConfigurationSettings:
    root: Path
    filename: str = 'tools_configuration.json.gz'


class FileToolConfigurationStore:
    def __init__(self, settings: FileToolConfigurationSettings) -> None:
        self._settings = settings

    def fetch_bundle(self) -> ToolConfigurationBundle | None:
        source = self._load_source()
        return source.current_bundle() if source is not None else None

    def publish_bundle(self, bundle: ToolConfigurationBundle) -> None:
        try:
            current = self._load_source()
            updated = (
                ToolConfigurationSourceDocument.from_bundle(bundle)
                if current is None
                else current.publish(bundle)
            )
            if current == updated:
                return
            _atomic_write_bytes(self._path, encode_tool_configuration_source(updated))
        except ToolConfigurationSourceError:
            raise
        except Exception as error:
            raise ToolConfigurationPublisherError(
                'Could not publish local tool configuration'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> ToolConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> ToolConfigurationSourceDocument | None:
        if not self._path.exists():
            return None
        try:
            return decode_tool_configuration_source(self._path.read_bytes())
        except Exception as error:
            raise ToolConfigurationSourceError(
                'Local tool configuration source is invalid'
            ) from error

    @property
    def _path(self) -> Path:
        return self._settings.root / self._settings.filename


@dataclass(frozen=True, slots=True)
class FileToolProjectionSettings:
    root: Path
    projection_filename: str = 'tools.json'
    item_id: str = 'tools'
    partition_key: str = 'tools'


class FileToolProjectionRepository:
    def __init__(self, settings: FileToolProjectionSettings) -> None:
        self._settings = settings

    def load(self) -> ToolConfigurationProjection | None:
        path = self._projection_path
        if not path.exists():
            return None
        try:
            return ToolConfigurationProjection.from_document(_read_json(path))
        except Exception as error:
            raise ToolConfigurationProjectionError(
                'Local tool projection is invalid'
            ) from error

    def save(self, projection: ToolConfigurationProjection) -> ToolConfigurationProjection:
        try:
            _atomic_write_json(
                self._projection_path,
                projection.to_document(
                    item_id=self._settings.item_id,
                    partition_key=self._settings.partition_key,
                ),
            )
        except Exception as error:
            raise ToolConfigurationProjectionError(
                'Could not write local tool projection'
            ) from error
        return projection

    def health_check(self) -> bool:
        try:
            self._settings.root.mkdir(parents=True, exist_ok=True)
            return os.access(self._settings.root, os.R_OK | os.W_OK)
        except OSError:
            return False

    @property
    def _projection_path(self) -> Path:
        return self._settings.root / self._settings.projection_filename


def _read_json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict):
        raise TypeError
    return document


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
