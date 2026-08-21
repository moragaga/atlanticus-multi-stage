# Implementa el History SharePoint de Tools y relee el manifest justo antes de escribir para detectar cambios remotos.
# No proyecta ni fuerza escrituras: una revisión distinta produce conflicto y preserva la fuente existente.

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Protocol

from ada.configuration.tools.bundle import (
    ToolConfigurationBundle,
    ToolConfigurationSourceDocument,
    decode_tool_configuration_source,
    encode_tool_configuration_source,
)
from ada.configuration.tools.errors import (
    ToolConfigurationPublisherError,
    ToolConfigurationSourceError,
)


class SharePointFileGateway(Protocol):
    def read(self, *, filename: str, relative_path: str) -> str | None: ...

    def write(self, *, filename: str, relative_path: str, content: str) -> None: ...


@dataclass(frozen=True, slots=True)
class SharePointToolConfigurationSettings:
    filename: str = 'tools_configuration.json.gz'
    relative_path: str = 'tools'

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError('SharePoint tool filename must not be empty')
        if not self.relative_path.strip():
            raise ValueError('SharePoint tool relative path must not be empty')


class SharePointToolConfigurationStore:
    def __init__(
        self,
        *,
        gateway: SharePointFileGateway,
        settings: SharePointToolConfigurationSettings,
    ) -> None:
        self._gateway = gateway
        self._settings = settings

    def fetch_bundle(self) -> ToolConfigurationBundle | None:
        source = self._load_source()
        return source.current_bundle() if source is not None else None

    def publish_bundle(
        self,
        bundle: ToolConfigurationBundle,
        *,
        expected_source_revision: str | None,
    ) -> None:
        try:
            current = self._load_source()
            current_bundle = current.current_bundle() if current is not None else None
            current_revision = current_bundle.revision if current_bundle is not None else None
            if current_revision != expected_source_revision:
                raise ToolConfigurationSourceError(
                    'Tool source revision changed before publication'
                )
            updated = (
                ToolConfigurationSourceDocument.from_bundle(bundle)
                if current is None
                else current.publish(bundle)
            )
            if current == updated:
                return
            content = base64.b64encode(encode_tool_configuration_source(updated)).decode('ascii')
            self._write_content(content)
        except ToolConfigurationPublisherError, ToolConfigurationSourceError:
            raise
        except Exception as error:
            raise ToolConfigurationPublisherError(
                'Could not publish tool configuration to SharePoint'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[ToolConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> ToolConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> ToolConfigurationSourceDocument | None:
        content = self._fetch_content()
        if content is None:
            return None
        try:
            payload = base64.b64decode(content, validate=True)
            return decode_tool_configuration_source(payload)
        except Exception as error:
            raise ToolConfigurationSourceError(
                'SharePoint tool configuration content is invalid'
            ) from error

    def _fetch_content(self) -> str | None:
        try:
            return self._gateway.read(
                filename=self._settings.filename,
                relative_path=self._settings.relative_path,
            )
        except Exception as error:
            raise ToolConfigurationSourceError(
                'Could not load tool configuration from SharePoint'
            ) from error

    def _write_content(self, content: str) -> None:
        try:
            self._gateway.write(
                filename=self._settings.filename,
                relative_path=self._settings.relative_path,
                content=content,
            )
        except Exception as error:
            raise ToolConfigurationPublisherError(
                'Could not publish tool configuration to SharePoint'
            ) from error
