from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ada.compositions.surface import AdaSurfaceComposition, AdaSurfaceResolution

if TYPE_CHECKING:
    # El tipo del Manager sólo ayuda al análisis estático; no crea una dependencia runtime.
    from ada.compositions.manager_surface import AdaManagerSurfaceComposition


@dataclass(frozen=True, slots=True)
class AdaApplicationComposition:
    # La aplicación recibe una resolución operacional ya decidida por el composition root concreto.
    operational_resolution: AdaSurfaceResolution
    # La administración es transversal pero opcional para el arranque operacional.
    manager: AdaManagerSurfaceComposition | None = None
    # El host recibe el prefijo desde el consumidor; nunca fija una ruta concreta como /manager.
    administration_route_prefix: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operational_resolution, AdaSurfaceResolution):
            raise TypeError('operational_resolution must be AdaSurfaceResolution')
        if self.administration_route_prefix is not None:
            if not isinstance(self.administration_route_prefix, str):
                raise TypeError('administration_route_prefix must be text or None')
            normalized = self.administration_route_prefix.strip()
            if not normalized or not normalized.startswith('/'):
                raise ValueError('administration_route_prefix must be an absolute route prefix')
            if normalized != self.administration_route_prefix:
                raise ValueError(
                    'administration_route_prefix must not contain surrounding whitespace'
                )

    @property
    def operational(self) -> AdaSurfaceComposition:
        # El host sólo necesita la surface resuelta, sin conocer el adapter concreto que la produjo.
        return self.operational_resolution.surface
