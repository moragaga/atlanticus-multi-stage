from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from atlanticus.web.users.activity.errors import UsersActivityConflictError, UsersActivityError
from atlanticus.web.users.activity.models import UserActivityDocument


class CosmosUserActivityClient(Protocol):
    def find_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
        include_metadata: bool = False,
    ) -> dict[str, Any] | None: ...

    def create_item(
        self,
        *,
        container_name: str,
        item: dict[str, Any],
        include_metadata: bool = False,
    ) -> dict[str, Any]: ...

    def replace_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
        item: dict[str, Any],
        if_match_etag: str | None = None,
        include_metadata: bool = False,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class CosmosUserActivitySettings:
    container_name: str = 'user_activity'

    def __post_init__(self) -> None:
        if not self.container_name.strip():
            raise UsersActivityError('User activity Cosmos container name must not be empty')


class CosmosUserActivityRepository:
    def __init__(
        self,
        *,
        client: CosmosUserActivityClient,
        settings: CosmosUserActivitySettings | None = None,
    ) -> None:
        self._client = client
        self._settings = settings or CosmosUserActivitySettings()

    def find(self, document_id: str) -> tuple[UserActivityDocument, str] | None:
        try:
            raw = self._client.find_item(
                container_name=self._settings.container_name,
                item_id=document_id,
                partition_key=document_id,
                include_metadata=True,
            )
        except Exception as error:
            raise UsersActivityError('Could not read user activity session from Cosmos') from error
        if raw is None:
            return None
        etag = str(raw.get('_etag') or '').strip()
        if not etag:
            raise UsersActivityError('Cosmos user activity session does not contain an ETag')
        return UserActivityDocument.from_document(raw), etag

    def create(self, document: UserActivityDocument) -> None:
        try:
            self._client.create_item(
                container_name=self._settings.container_name,
                item=document.to_document(),
            )
        except Exception as error:
            if _is_concurrency_conflict(error):
                raise UsersActivityConflictError(
                    'User activity session changed concurrently'
                ) from error
            raise UsersActivityError('Could not create user activity session in Cosmos') from error

    def replace(self, document: UserActivityDocument, *, etag: str) -> None:
        try:
            self._client.replace_item(
                container_name=self._settings.container_name,
                item_id=document.id,
                partition_key=document.id,
                item=document.to_document(),
                if_match_etag=etag,
            )
        except Exception as error:
            if _is_concurrency_conflict(error):
                raise UsersActivityConflictError(
                    'User activity session changed concurrently'
                ) from error
            raise UsersActivityError('Could not update user activity session in Cosmos') from error


def _is_concurrency_conflict(error: BaseException) -> bool:
    status_code = getattr(error, 'status_code', None)
    if status_code in {409, 412}:
        return True
    return type(error).__name__ in {
        'CosmosConflictError',
        'CosmosPreconditionFailedError',
        'ResourceExistsError',
        'ResourceModifiedError',
    }
