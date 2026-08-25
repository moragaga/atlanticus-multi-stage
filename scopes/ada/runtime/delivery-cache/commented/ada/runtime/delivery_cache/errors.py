# Errores de definición del contrato o de consistencia del snapshot compartido.
class DeliveryCacheDefinitionError(ValueError):
    pass


class DeliveryCacheConsistencyError(RuntimeError):
    pass
