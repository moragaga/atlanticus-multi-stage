from __future__ import annotations

from atlanticus.web.services import ServiceRegistry
from integrated_operations.application.models import IntegratedOperationsApplicationComposition
from integrated_operations.application.presentation import build_unified_application_layout


# El layout productivo delega en la nueva presentación unificada.
def build_application_layout(
    services: ServiceRegistry,
    *,
    composition: IntegratedOperationsApplicationComposition,
):
    return build_unified_application_layout(services, composition=composition)
