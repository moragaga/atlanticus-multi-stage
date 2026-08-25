# Implementa Source/History y Projection KPI locales en raíces separadas.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from ada.configuration.kpis.bundle import (
    KpiConfigurationBundle,
    KpiConfigurationSourceDocument,
    decode_kpi_configuration_source,
    encode_kpi_configuration_source,
)
from ada.configuration.kpis.errors import (
    KpiConfigurationProjectionError,
    KpiConfigurationPublisherError,
    KpiConfigurationSourceError,
)
from ada.configuration.kpis.projection import KpiConfigurationProjection


@dataclass(frozen=True, slots=True)
class FileKpiConfigurationSettings:
    root: Path
    filename: str = 'kpi_configuration.json.gz'


class FileKpiConfigurationStore:
    def __init__(self, settings: FileKpiConfigurationSettings) -> None:
        self._settings = settings

    def fetch_bundle(self) -> KpiConfigurationBundle | None:
        source = self._load_source()
        return source.current_bundle() if source is not None else None

    def publish_bundle(
        self,
        bundle: KpiConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None:
        try:
            current = self._load_source()
            current_bundle = current.current_bundle() if current is not None else None
            current_revision = current_bundle.revision if current_bundle is not None else None
            if current_revision != expected_source_revision:
                raise KpiConfigurationSourceError('KPI source revision changed before publication')
            updated = (
                KpiConfigurationSourceDocument.from_bundle(bundle)
                if current is None
                else current.publish(bundle)
            )
            if current == updated:
                return
            _atomic_write_bytes(self._path, encode_kpi_configuration_source(updated))
        except KpiConfigurationSourceError:
            raise
        except Exception as error:
            raise KpiConfigurationPublisherError(
                'Could not publish local KPI configuration'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[KpiConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> KpiConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> KpiConfigurationSourceDocument | None:
        if not self._path.exists():
            return None
        try:
            return decode_kpi_configuration_source(self._path.read_bytes())
        except Exception as error:
            raise KpiConfigurationSourceError(
                'Local KPI configuration source is invalid'
            ) from error

    @property
    def _path(self) -> Path:
        return self._settings.root / self._settings.filename


@dataclass(frozen=True, slots=True)
class FileKpiProjectionSettings:
    root: Path
    projection_filename: str = 'kpis.json'
    item_id: str = 'kpis'
    partition_key: str = 'kpis'


class FileKpiProjectionRepository:
    def __init__(self, settings: FileKpiProjectionSettings) -> None:
        self._settings = settings

    def load(self) -> KpiConfigurationProjection | None:
        path = self._projection_path
        if not path.exists():
            return None
        try:
            return KpiConfigurationProjection.from_document(_read_json(path))
        except Exception as error:
            raise KpiConfigurationProjectionError('Local KPI projection is invalid') from error

    def save(self, projection: KpiConfigurationProjection) -> KpiConfigurationProjection:
        try:
            _atomic_write_json(
                self._projection_path,
                projection.to_document(
                    item_id=self._settings.item_id,
                    partition_key=self._settings.partition_key,
                ),
            )
        except Exception as error:
            raise KpiConfigurationProjectionError('Could not write local KPI projection') from error
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
