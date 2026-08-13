# Espejo comentado de los errores contractuales del runtime web ADA.
# Mantiene el mismo AST que la implementación productiva.
class RuntimeDefinitionError(ValueError):
    """Raised when an ADA runtime contract is structurally invalid."""
