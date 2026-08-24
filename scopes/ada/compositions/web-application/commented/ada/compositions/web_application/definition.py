from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path

from ada.ui.shell.navigation import create_ada_navigation_module
from atlanticus.web.assets import AssetLayer
from atlanticus.web.index import IndexPageDefinition
from atlanticus.web.models import ApplicationMetadata, WebApplicationDefinition
from atlanticus.web.modules import WebModule

from .models import AdaApplicationComposition
from .presentation import build_ada_application_layout, create_ada_application_presentation_module


def build_ada_web_definition(
    *,
    import_name: str,
    metadata: ApplicationMetadata,
    deployment_modules: Sequence[WebModule],
    composition: AdaApplicationComposition,
    page_packages: Sequence[str],
    asset_layers: Sequence[AssetLayer] = (),
    flask_config: Mapping[str, object] | None = None,
) -> WebApplicationDefinition:
    # Los módulos transversales del deployment se registran antes de los consumidores de servicios.
    modules = [
        *deployment_modules,
        # Operational aporta módulos desde la surface ya resuelta, sin importar su implementación.
        *composition.operational.modules,
        # Navigation es una única shell compartida por toda la aplicación ADA.
        create_ada_navigation_module(),
    ]
    if composition.manager is not None:
        # Manager agrega sólo sus módulos cuando realmente fue compuesto.
        modules.extend(composition.manager.web_modules)
    # La presentación común se registra al final porque consume las composiciones anteriores.
    modules.append(create_ada_application_presentation_module(composition))
    return WebApplicationDefinition(
        # El import name, páginas y assets concretos pertenecen al composition root consumidor.
        import_name=import_name,
        metadata=metadata,
        publications_root=Path.cwd() / '.runtime' / 'assets',
        layout=partial(build_ada_application_layout, composition=composition),
        modules=tuple(modules),
        page_packages=tuple(page_packages),
        asset_layers=tuple(asset_layers),
        index=IndexPageDefinition(language='es'),
        flask_config=dict(flask_config or {}),
    )
