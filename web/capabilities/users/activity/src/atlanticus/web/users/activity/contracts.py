from typing import Protocol

from atlanticus.web.users.activity.models import UserActivityDocument


class UserActivityRepository(Protocol):
    def find(self, document_id: str) -> tuple[UserActivityDocument, str] | None: ...

    def create(self, document: UserActivityDocument) -> None: ...

    def replace(self, document: UserActivityDocument, *, etag: str) -> None: ...
