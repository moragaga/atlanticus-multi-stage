# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Usa un único GET/POST lógico para current, versiones y auditoría de Tools.
from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass

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

JsonPostOperation = Callable[[dict[str, object]], object]


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
        post_json: JsonPostOperation,
        settings: SharePointToolConfigurationSettings,
    ) -> None:
        self._post_json = post_json
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
            content = base64.b64encode(encode_tool_configuration_source(updated)).decode('ascii')
            self._write_content(content)
        except (ToolConfigurationPublisherError, ToolConfigurationSourceError):
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
            response = self._post_json(
                {
                    'filename': self._settings.filename,
                    'relative_path': self._settings.relative_path,
                }
            )
        except Exception as error:
            raise ToolConfigurationSourceError(
                'Could not load tool configuration from SharePoint'
            ) from error
        if not isinstance(response, Mapping):
            raise ToolConfigurationSourceError(
                'SharePoint tool configuration response must be an object'
            )
        content = response.get('content')
        if content is None:
            return None
        if not isinstance(content, str):
            raise ToolConfigurationSourceError(
                'SharePoint tool configuration content must be text'
            )
        return content.strip() or None

    def _write_content(self, content: str) -> None:
        try:
            self._post_json(
                {
                    'filename': self._settings.filename,
                    'relative_path': self._settings.relative_path,
                    'content': content,
                }
            )
        except Exception as error:
            raise ToolConfigurationPublisherError(
                'Could not publish tool configuration to SharePoint'
            ) from error
