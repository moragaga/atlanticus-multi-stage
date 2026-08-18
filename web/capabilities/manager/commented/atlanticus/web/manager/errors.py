# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Capability genérica del Configuration Manager de Atlanticus. Mantiene contratos y UI administrativa sin conocer dominios ni persistencias concretas.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

class ManagerError(Exception):
    pass


class ManagerDefinitionError(ManagerError):
    pass


class ManagerAuthorizationError(ManagerError):
    pass


class ManagerProjectionError(ManagerError):
    pass
