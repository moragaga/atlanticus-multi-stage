# Errores específicos permiten diferenciar fallas de registro/resolución sin acoplarse a una app concreta.
class AdaSurfaceError(ValueError):
    pass


class AdaSurfaceAdapterError(AdaSurfaceError):
    pass


class AdaSurfaceLookupError(AdaSurfaceError):
    pass
