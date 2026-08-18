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
