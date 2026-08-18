# Espejo pedagógico: Implementa tracking funcional de usuarios: identidad, perfil observado, rutas estables, resolución de pantalla y tiempo activo.

from typing import Protocol

from atlanticus.web.users.activity.models import UserActivityDocument


class UserActivityRepository(Protocol):
    def find(self, document_id: str) -> tuple[UserActivityDocument, str] | None: ...

    def create(self, document: UserActivityDocument) -> None: ...

    def replace(self, document: UserActivityDocument, *, etag: str) -> None: ...
