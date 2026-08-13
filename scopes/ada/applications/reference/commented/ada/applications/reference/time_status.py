# La composition root obtiene el runtime y entrega al shell un estado ya resuelto.
from ada.applications.reference.runtime import ADA_RUNTIME_SERVICE
from ada.contracts.tool_manifest import ToolManifest
from ada.runtime.web import AdaRuntime
from ada.ui.shell.time_status import TimeStatusState, create_time_status_state
from atlanticus.web.services import ServiceRegistry


def build_reference_time_status_state(
    services: ServiceRegistry,
    manifest: ToolManifest,
) -> TimeStatusState:
    runtime = services.require(ADA_RUNTIME_SERVICE, AdaRuntime)
    return create_time_status_state(
        manifest=manifest,
        snapshot=runtime.current().snapshot,
    )
