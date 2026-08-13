from __future__ import annotations

from dash import html, page_container

from ada.applications.reference.header import build_reference_header_state
from ada.contracts.tool_manifest import ToolManifestResolution, ToolManifestResolutionStatus
from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper
from ada.ui.framework.core import build_ready_scope, ready_attributes
from ada.ui.shell.header import build_ada_header
from ada.ui.shell.navigation import (
    build_ada_navigation_desktop_trigger,
    build_ada_navigation_mobile_trigger,
    build_ada_navigation_offcanvas_from_services,
)
from atlanticus.web.services import ServiceRegistry


def build_layout(
    services: ServiceRegistry,
    *,
    tool_manifest_resolution: ToolManifestResolution,
) -> object:
    # La falta de configuración básica es un estado controlado y listo, no un fallo de startup.
    if not tool_manifest_resolution.ready:
        return _build_configuration_fallback(tool_manifest_resolution)

    manifest = tool_manifest_resolution.require_manifest()
    content = html.Div(
        [
            build_ada_header(
                build_reference_header_state(services, manifest),
                desktop_navigation_trigger=build_ada_navigation_desktop_trigger(),
                mobile_navigation_trigger=build_ada_navigation_mobile_trigger(),
            ),
            html.Div(
                build_ada_navigation_offcanvas_from_services(services),
                **ready_attributes('navigation', ready=True),
            ),
            html.Main(
                page_container,
                className='reference-ada__content',
            ),
        ],
        className='reference-ada',
    )
    return build_ready_scope(
        content=content,
        required=(
            'global-indicators',
            'alarm-management',
            'alarm-status',
            'navigation',
            'page-content',
        ),
    )


# El wrapper superior evita montar componentes cuya configuración aún no conocemos.
def _build_configuration_fallback(resolution: ToolManifestResolution) -> object:
    cover = {
        ToolManifestResolutionStatus.NOT_PROJECTED: ComponentCover.construction(
            message=(
                'Configuration not available. '
                'The basic configuration for this tool is not available yet.'
            )
        ),
        ToolManifestResolutionStatus.INVALID: ComponentCover.source_error(
            message='Configuration invalid. The basic configuration for this tool is invalid.'
        ),
        ToolManifestResolutionStatus.SOURCE_ERROR: ComponentCover.source_error(
            message=(
                'Configuration unavailable. '
                'The basic configuration for this tool could not be loaded.'
            )
        ),
    }[resolution.status]
    return build_ready_scope(
        content=build_state_wrapper(
            cover=cover,
            class_name='reference-ada__configuration-state',
            ready_name='tool-configuration',
        ),
        required=('tool-configuration',),
    )
