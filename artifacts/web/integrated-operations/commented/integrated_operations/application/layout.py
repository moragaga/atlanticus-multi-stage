# Espejo pedagógico: por ahora la presentación sigue mostrando sólo la superficie operacional; el Manager ya queda disponible para el siguiente incremento visual.
from __future__ import annotations

from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.models import IntegratedOperationsApplicationComposition
from integrated_operations.tool import build_integrated_operations_tool


def build_application_layout(
    _services: ServiceRegistry,
    *,
    composition: IntegratedOperationsApplicationComposition,
):
    return build_integrated_operations_tool(composition.operational)
