# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
class HeaderDefinitionError(ValueError):
    pass


class HeaderPresentationError(RuntimeError):
    pass
