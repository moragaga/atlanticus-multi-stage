from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from atlanticus.web.users.configuration.bundle import (
    UsersConfigurationBundle,
    UsersConfigurationSourceDocument,
    decode_users_configuration_source,
    encode_users_configuration_source,
)
from atlanticus.web.users.configuration.errors import (
    UsersConfigurationPublisherError,
    UsersConfigurationSourceError,
)

JsonPostOperation = Callable[[dict[str, object]], object]


@dataclass(frozen=True, slots=True)
class SharePointUsersConfigurationSettings:
    filename: str = 'users_configuration.json.gz'
    relative_path: str = 'users'

    def __post_init__(self) -> None:
        if not self.filename.strip():
            raise ValueError('SharePoint users filename must not be empty')
        if not self.relative_path.strip():
            raise ValueError('SharePoint users relative path must not be empty')


class SharePointUsersConfigurationStore:
    def __init__(
        self,
        *,
        post_json: JsonPostOperation,
        settings: SharePointUsersConfigurationSettings,
    ) -> None:
        self._post_json = post_json
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
            content = base64.b64encode(encode_users_configuration_source(updated)).decode('ascii')
            self._write_content(content)
        except UsersConfigurationPublisherError, UsersConfigurationSourceError:
            raise
        except Exception as error:
            raise UsersConfigurationPublisherError(
                'Could not publish users configuration to SharePoint'
            ) from error

    def list_history(self, *, limit: int = 20) -> tuple[UsersConfigurationBundle, ...]:
        source = self._load_source()
        return source.list_history(limit=limit) if source is not None else ()

    def fetch_revision(self, revision: str) -> UsersConfigurationBundle | None:
        source = self._load_source()
        return source.fetch_revision(revision) if source is not None else None

    def _load_source(self) -> UsersConfigurationSourceDocument | None:
        content = self._fetch_content()
        if content is None:
            return None
        try:
            payload = base64.b64decode(content, validate=True)
            return decode_users_configuration_source(payload)
        except Exception as error:
            raise UsersConfigurationSourceError(
                'SharePoint users configuration content is invalid'
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
            raise UsersConfigurationSourceError(
                'Could not load users configuration from SharePoint'
            ) from error
        if not isinstance(response, Mapping):
            raise UsersConfigurationSourceError(
                'SharePoint users configuration response must be an object'
            )
        content = response.get('content')
        if content is None:
            return None
        if not isinstance(content, str):
            raise UsersConfigurationSourceError(
                'SharePoint users configuration content must be text'
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
            raise UsersConfigurationPublisherError(
                'Could not publish users configuration to SharePoint'
            ) from error
