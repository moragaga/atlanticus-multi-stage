# Separa errores de validación, Source y Projection de KPI Configuration.
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
