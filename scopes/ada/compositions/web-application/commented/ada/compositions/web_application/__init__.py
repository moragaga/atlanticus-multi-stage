# La fachada pública reúne los contratos de aplicación y la composición transversal existente.
from ada.compositions.web_application.composition import create_ada_application_modules
from ada.compositions.web_application.definition import build_ada_web_definition
from ada.compositions.web_application.models import AdaApplicationComposition
from ada.compositions.web_application.presentation import (
    LOCATION_ID,
    SURFACE_HOST_ID,
    SURFACE_LOADING_ID,
    build_ada_application_layout,
    build_application_surface,
    create_ada_application_presentation_module,
)

__all__ = [
    'AdaApplicationComposition',
    'LOCATION_ID',
    'SURFACE_HOST_ID',
    'SURFACE_LOADING_ID',
    'build_ada_application_layout',
    'build_ada_web_definition',
    'build_application_surface',
    'create_ada_application_modules',
    'create_ada_application_presentation_module',
]
