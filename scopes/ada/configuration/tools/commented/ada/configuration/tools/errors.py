# Espejo pedagógico: este archivo conserva exactamente la lógica del código productivo.
# Configuración de herramientas del scope ADA. Convierte datos administrativos mínimos en contratos runtime ToolManifest sin acoplar el dominio a la UI.
# Los comentarios explican la intención arquitectónica; no agregan ramas, estado ni comportamiento.

class ToolConfigurationError(Exception):
    pass


class ToolConfigurationValidationError(ToolConfigurationError):
    pass


class ToolConfigurationSourceError(ToolConfigurationError):
    pass


class ToolConfigurationPublisherError(ToolConfigurationError):
    pass


class ToolConfigurationProjectionError(ToolConfigurationError):
    pass
