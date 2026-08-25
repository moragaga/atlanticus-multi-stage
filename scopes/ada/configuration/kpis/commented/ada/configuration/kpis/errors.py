# Mantiene una jerarquía de errores propia para separar validación, Source y Projection.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
class KpiConfigurationError(RuntimeError):
    pass


class KpiConfigurationValidationError(KpiConfigurationError):
    pass


class KpiConfigurationSourceError(KpiConfigurationError):
    pass


class KpiConfigurationPublisherError(KpiConfigurationError):
    pass


class KpiConfigurationProjectionError(KpiConfigurationError):
    pass
