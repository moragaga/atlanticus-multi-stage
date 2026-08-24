# Expone únicamente el contrato público necesario para componer el Manager dentro de ADA.
from .composition import (
    AdaManagerSurfaceComposition,
    create_ada_manager_surface_composition,
)

__all__ = [
    'AdaManagerSurfaceComposition',
    'create_ada_manager_surface_composition',
]
