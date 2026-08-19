# Espejo pedagógico: Source SharePoint mediante la operación POST genérica de Power Automate.
from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from atlanticus.web.navigation.configuration.bundle import (
    NavigationConfigurationBundle,
    NavigationConfigurationSourceDocument,
    decode_navigation_configuration_source,
    encode_navigation_configuration_source,
)
from atlanticus.web.navigation.configuration.errors import (
    NavigationConfigurationPublisherError,
    NavigationConfigurationSourceError,
)

JsonPostOperation = Callable[[dict[str, object]], object]


@dataclass(frozen=True, slots=True)
class SharePointNavigationConfigurationSettings:
    filename: str = 'navigation_configuration.json.gz'
    relative_path: str = 'navigation'

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError('SharePoint navigation filename must not be empty')
        if not self.relative_path.strip():
            raise ValueError('SharePoint navigation relative path must not be empty')


class SharePointNavigationConfigurationStore:
    def __init__(
        self,
        *,
        post_json: JsonPostOperation,
        settings: SharePointNavigationConfigurationSettings,
    ) -> None:
        self._post_json = post_json
        self._settings = settings

    def fetch_bundle(self) -> NavigationConfigurationBundle | None:
        source = self._load_source()
        return source.current_bundle() if source is not None else None

    def publish_bundle(self, bundle: NavigationConfigurationBundle) -> None:
        try:
            current = self._load_source()
            updated = (
                NavigationConfigurationSourceDocument.from_bundle(bundle)
                if current is None
                else current.publish(bundle)
            )
            if current == updated:
                return
            content = base64.b64encode(
                encode_navigation_configuration_source(updated)
            ).decode('ascii')
            self._write_content(content)
        except (NavigationConfigurationPublisherError, NavigationConfigurationSourceError):
            raise
        except Exception as error:
            raise NavigationConfigurationPublisherError(
                'Could not publish navigation configuration to SharePoint'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[NavigationConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> NavigationConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> NavigationConfigurationSourceDocument | None:
        content = self._fetch_content()
        if content is None:
            return None
        try:
            payload = base64.b64decode(content, validate=True)
            return decode_navigation_configuration_source(payload)
        except Exception as error:
            raise NavigationConfigurationSourceError(
                'SharePoint navigation configuration content is invalid'
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
            raise NavigationConfigurationSourceError(
                'Could not load navigation configuration from SharePoint'
            ) from error
        if not isinstance(response, Mapping):
            raise NavigationConfigurationSourceError(
                'SharePoint navigation configuration response must be an object'
            )
        content = response.get('content')
        if content is None:
            return None
        if not isinstance(content, str):
            raise NavigationConfigurationSourceError(
                'SharePoint navigation configuration content must be text'
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
            raise NavigationConfigurationPublisherError(
                'Could not publish navigation configuration to SharePoint'
            ) from error
