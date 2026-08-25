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
