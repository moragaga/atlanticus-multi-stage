# Espejo comentado de los errores contractuales y de consistencia del runtime web ADA.
# Los mensajes productivos permanecen en inglés para facilitar observabilidad y soporte.
class RuntimeDefinitionError(ValueError):
    """Raised when an ADA runtime contract is structurally invalid."""


# Se usa cuando el repositorio anuncia una revisión y entrega un snapshot de otra publicación.
# La caché local nunca reemplaza su último snapshot válido ante esta inconsistencia.
class SharedSnapshotConsistencyError(RuntimeError):
    """Raised when a shared snapshot does not match its advertised revision."""
