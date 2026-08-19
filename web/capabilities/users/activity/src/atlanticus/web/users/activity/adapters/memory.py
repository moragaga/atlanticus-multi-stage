from __future__ import annotations

from threading import RLock

from atlanticus.web.users.activity.errors import UsersActivityConflictError
from atlanticus.web.users.activity.models import UserActivityDocument


class InMemoryUserActivityRepository:
    def __init__(self) -> None:
        self._documents: dict[str, tuple[UserActivityDocument, int]] = {}
        self._lock = RLock()

    def find(self, document_id: str) -> tuple[UserActivityDocument, str] | None:
        with self._lock:
            found = self._documents.get(document_id)
            if found is None:
                return None
            document, revision = found
            return document, str(revision)

    def create(self, document: UserActivityDocument) -> None:
        with self._lock:
            if document.id in self._documents:
                raise UsersActivityConflictError('User activity session already exists')
            self._documents[document.id] = (document, 1)

    def replace(self, document: UserActivityDocument, *, etag: str) -> None:
        with self._lock:
            found = self._documents.get(document.id)
            if found is None or str(found[1]) != etag:
                raise UsersActivityConflictError('User activity session changed concurrently')
            self._documents[document.id] = (document, found[1] + 1)

    def snapshot(self) -> tuple[UserActivityDocument, ...]:
        with self._lock:
            return tuple(document for document, _revision in self._documents.values())
