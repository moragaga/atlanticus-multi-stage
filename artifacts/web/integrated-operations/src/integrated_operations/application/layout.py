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
