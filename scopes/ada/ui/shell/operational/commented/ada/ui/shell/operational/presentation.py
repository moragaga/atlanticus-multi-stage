from __future__ import annotations

from collections.abc import Mapping, Sequence

from dash import html
from dash.development.base_component import Component

from ada.contracts.tool_manifest import ToolManifest
from ada.features.alarms.management_summary import build_alarm_management_summary
from ada.features.alarms.notifications import build_alarm_status
from ada.ui.components.state_wrapper import ComponentCover, build_state_wrapper
from ada.ui.framework.core import build_ready_scope
from ada.ui.shell.header import HeaderState, build_ada_header
from ada.ui.shell.time_status import TimeStatusState, build_ada_time_status

from .errors import OperationalShellError

# La base conserva los readiness contracts ya usados por las composiciones actuales.
_DEFAULT_READY_REQUIRED = (
    'global-indicators',
    'alarm-management',
    'alarm-status',
    'time-status',
)
_RESERVED_ROOT_ATTRIBUTES = {
    'children',
    'className',
    'style',
    'data-ada-operational-shell',
}
_RESERVED_ALARM_ATTRIBUTES = {
    'children',
    'className',
}


def build_ada_operational_shell(
    manifest: ToolManifest,
    *,
    header_state: HeaderState,
    body_content: Component | Sequence[Component] | None = None,
    alarm_children: Sequence[Component] = (),
    alarm_management_slot: Component | None = None,
    alarm_status_slot: Component | None = None,
    time_status_state: TimeStatusState | None = None,
    desktop_navigation_trigger: Component | None = None,
    mobile_navigation_trigger: Component | None = None,
    runtime_hosts: Sequence[Component] = (),
    runtime_component_wrapper_ids: Mapping[str, str] | None = None,
    shell_class_name: str | None = None,
    time_status_class_name: str | None = None,
    alarm_surface_class_name: str | None = None,
    body_class_name: str | None = None,
    shell_style: Mapping[str, object] | None = None,
    shell_attributes: Mapping[str, object] | None = None,
    alarm_surface_attributes: Mapping[str, object] | None = None,
    ready_required: tuple[str, ...] = _DEFAULT_READY_REQUIRED,
) -> html.Div:
    # El shell valida sólo identidad común; la geometría específica sigue en la surface concreta.
    _validate_manifest(manifest)
    _validate_header_state(manifest, header_state)
    _validate_time_status_state(manifest, time_status_state)
    root_attributes = _validated_attributes(
        shell_attributes,
        reserved=_RESERVED_ROOT_ATTRIBUTES,
        field_name='shell attributes',
    )
    alarm_attributes = _validated_attributes(
        alarm_surface_attributes,
        reserved=_RESERVED_ALARM_ATTRIBUTES,
        field_name='alarm surface attributes',
    )
    # Time Status es un componente runtime real, pero su id se omite mientras no exista binding.
    time_status_attributes: dict[str, object] = {
        'className': _join_classes(
            'ada-operational-shell__time-status',
            time_status_class_name,
        )
    }
    time_status_wrapper_id = _runtime_wrapper_id(
        runtime_component_wrapper_ids,
        'time_status',
    )
    if time_status_wrapper_id is not None:
        time_status_attributes['id'] = time_status_wrapper_id

    # Header, estado temporal, alarmas y body conservan siempre la misma secuencia vertical.
    shell_children: list[Component] = [
        build_ada_header(
            header_state,
            alarm_management_slot=(
                alarm_management_slot
                if alarm_management_slot is not None
                else build_alarm_management_summary(
                    None,
                    cover=ComponentCover.construction(),
                )
            ),
            alarm_status_slot=(
                alarm_status_slot
                if alarm_status_slot is not None
                else build_alarm_status(
                    None,
                    cover=ComponentCover.construction(),
                )
            ),
            desktop_navigation_trigger=desktop_navigation_trigger,
            mobile_navigation_trigger=mobile_navigation_trigger,
            runtime_component_wrapper_ids=runtime_component_wrapper_ids,
        ),
        html.Div(
            _build_time_status(manifest, time_status_state),
            **time_status_attributes,
        ),
        html.Section(
            list(alarm_children),
            className=_join_classes(
                'ada-operational-shell__alarm-surface',
                alarm_surface_class_name,
            ),
            **alarm_attributes,
        ),
        html.Main(
            body_content,
            className=_join_classes('ada-operational-shell__body', body_class_name),
        ),
    ]
    # Los hosts runtime se agregan fuera de la geometría visible para no alterar la UI existente.
    shell_children.extend(tuple(runtime_hosts))

    root_properties: dict[str, object] = {
        'className': _join_classes('ada-operational-shell', shell_class_name),
        'data-ada-operational-shell': manifest.tool_key,
        **root_attributes,
    }
    if shell_style is not None:
        root_properties['style'] = dict(shell_style)
    root = html.Div(
        shell_children,
        **root_properties,
    )
    return build_ready_scope(
        content=root,
        required=ready_required,
    )


def _runtime_wrapper_id(
    wrapper_ids: Mapping[str, str] | None,
    component_key: str,
) -> str | None:
    # Un binding ausente es válido; un binding presente pero vacío es un error contractual.
    if wrapper_ids is None:
        return None
    value = wrapper_ids.get(component_key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise OperationalShellError(
            f'Invalid runtime wrapper id for operational component {component_key!r}'
        )
    return value.strip()


def _build_time_status(
    manifest: ToolManifest,
    state: TimeStatusState | None,
) -> Component:
    if state is None:
        return build_state_wrapper(
            cover=ComponentCover.construction(),
            ready_name='time-status',
        )
    _validate_time_status_state(manifest, state)
    return build_state_wrapper(
        content=build_ada_time_status(state),
        ready_name='time-status',
    )


def _validate_manifest(manifest: ToolManifest) -> None:
    if not isinstance(manifest, ToolManifest):
        raise OperationalShellError(f'Invalid operational tool manifest: {manifest!r}')


def _validate_header_state(manifest: ToolManifest, state: HeaderState) -> None:
    if not isinstance(state, HeaderState):
        raise OperationalShellError(f'Invalid operational header state: {state!r}')
    if state.tool_key != manifest.tool_key:
        raise OperationalShellError('Header state tool key does not match operational manifest')


def _validate_time_status_state(
    manifest: ToolManifest,
    state: TimeStatusState | None,
) -> None:
    if state is None:
        return
    if not isinstance(state, TimeStatusState):
        raise OperationalShellError(f'Invalid operational time status state: {state!r}')
    if state.tool_key != manifest.tool_key:
        raise OperationalShellError('Time status tool key does not match operational manifest')


def _validated_attributes(
    values: Mapping[str, object] | None,
    *,
    reserved: set[str],
    field_name: str,
) -> dict[str, object]:
    resolved = {} if values is None else dict(values)
    conflicts = sorted(reserved & resolved.keys())
    if conflicts:
        raise OperationalShellError(f'Reserved {field_name}: {", ".join(conflicts)}')
    return resolved


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
