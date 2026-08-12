# Error de validación estructural del manifiesto.
class ToolManifestError(ValueError):
    pass


# Error de búsqueda para herramientas, secciones o destinos inexistentes.
class ToolManifestLookupError(LookupError):
    pass
