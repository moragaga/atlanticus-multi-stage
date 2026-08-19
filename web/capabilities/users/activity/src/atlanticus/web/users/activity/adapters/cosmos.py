from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from atlanticus.web.users.activity.errors import UsersActivityConflictError, UsersActivityError
from atlanticus.web.users.activity.models import UserActivityDocument

COSMOS_USER_ACTIVITY_RECORD_TYPE = 'user_activity_record'
COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION = 1
COSMOS_USER_ACTIVITY_PAYLOAD_PATH = '/payload'

PatchOperationT = TypeVar('PatchOperationT')


class CosmosUserActivityClient(Protocol[PatchOperationT]):
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
        item: Mapping[str, Any],
        include_metadata: bool = False,
    ) -> dict[str, Any]: ...

    def patch_item(
        self,
        *,
        container_name: str,
        item_id: str,
        partition_key: object,
        operations: Sequence[PatchOperationT],
        if_match_etag: str | None = None,
        include_metadata: bool = False,
    ) -> dict[str, Any]: ...


class CosmosUserActivityPatchOperationFactory(Protocol[PatchOperationT]):
    def __call__(
        self,
        *,
        operation: str,
        path: str,
        value: Any,
    ) -> PatchOperationT: ...


@dataclass(frozen=True, slots=True)
class CosmosUserActivitySettings:
    container_name: str = 'user_activity'

    def __post_init__(self) -> None:
        if not self.container_name.strip():
            raise UsersActivityError('User activity Cosmos container name must not be empty')


class CosmosUserActivityRepository(Generic[PatchOperationT]):
    def __init__(
        self,
        *,
        client: CosmosUserActivityClient[PatchOperationT],
        patch_operation_factory: CosmosUserActivityPatchOperationFactory[PatchOperationT],
        settings: CosmosUserActivitySettings | None = None,
    ) -> None:
        self._client = client
        self._patch_operation_factory = patch_operation_factory
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
        return _document_from_record(raw, document_id=document_id), etag

    def create(self, document: UserActivityDocument) -> None:
        try:
            self._client.create_item(
                container_name=self._settings.container_name,
                item=_record_from_document(document),
            )
        except Exception as error:
            if _is_concurrency_conflict(error):
                raise UsersActivityConflictError(
                    'User activity session changed concurrently'
                ) from error
            raise UsersActivityError('Could not create user activity session in Cosmos') from error

    def replace(self, document: UserActivityDocument, *, etag: str) -> None:
        operation = self._patch_operation_factory(
            operation='set',
            path=COSMOS_USER_ACTIVITY_PAYLOAD_PATH,
            value=document.to_document(),
        )
        try:
            self._client.patch_item(
                container_name=self._settings.container_name,
                item_id=document.id,
                partition_key=document.id,
                operations=(operation,),
                if_match_etag=etag,
            )
        except Exception as error:
            if _is_concurrency_conflict(error):
                raise UsersActivityConflictError(
                    'User activity session changed concurrently'
                ) from error
            raise UsersActivityError('Could not update user activity session in Cosmos') from error


def _record_from_document(document: UserActivityDocument) -> dict[str, Any]:
    return {
        'id': document.id,
        'type': COSMOS_USER_ACTIVITY_RECORD_TYPE,
        'storage_schema_version': COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
        'payload': document.to_document(),
    }


def _document_from_record(
    value: Mapping[str, Any],
    *,
    document_id: str,
) -> UserActivityDocument:
    if value.get('type') != COSMOS_USER_ACTIVITY_RECORD_TYPE:
        raise UsersActivityError('Cosmos user activity record type is invalid')
    if value.get('storage_schema_version') != COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION:
        raise UsersActivityError('Cosmos user activity storage schema is invalid')
    payload = value.get('payload')
    if not isinstance(payload, Mapping):
        raise UsersActivityError('Cosmos user activity payload is invalid')
    document = UserActivityDocument.from_document(payload)
    if document.id != document_id or value.get('id') != document_id:
        raise UsersActivityError('Cosmos user activity record identity is invalid')
    return document


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
