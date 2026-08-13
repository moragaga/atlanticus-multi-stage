"""Errores propios de definición y resolución de branding ADA."""


class BrandDefinitionError(ValueError):
    pass


class BrandResolutionError(LookupError):
    pass
