# Espejo pedagógico: Implementa tracking funcional de usuarios: identidad, perfil observado, rutas estables, resolución de pantalla y tiempo activo.

class UsersActivityError(Exception):
    pass


class UsersActivityConflictError(UsersActivityError):
    pass
