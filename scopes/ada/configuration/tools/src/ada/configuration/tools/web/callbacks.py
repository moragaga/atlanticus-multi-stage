from __future__ import annotations

import base64
from datetime import UTC, datetime

from dash import ALL, Input, Output, State, ctx, html, no_update

from ada.configuration.tools.builder import build_tool_manifest
from ada.configuration.tools.bundle import (
    build_tool_configuration_digest,
    decode_tool_configuration_import,
)
from ada.configuration.tools.identity import build_identity_key
from ada.configuration.tools.models import (
    ToolComponentConfiguration,
    ToolConfiguration,
    ToolConfigurationCatalog,
    ToolConfigurationKind,
    ToolSourceConfiguration,
    ToolSubcomponentConfiguration,
)
from ada.configuration.tools.web.ids import (
    ADD_COMPONENT_ID,
    ADD_SUBCOMPONENT_ID,
    APPLICATION_KEY_ID,
    CATALOG_STORE_ID,
    COMPONENT_CANCEL_ID,
    COMPONENT_EDITOR_STORE_ID,
    COMPONENT_MODAL_ID,
    COMPONENT_MODAL_RESULT_ID,
    COMPONENT_MODAL_TITLE_ID,
    COMPONENT_NAME_ID,
    COMPONENT_PLACEMENT_FIELD_ID,
    COMPONENT_PLACEMENT_ID,
    COMPONENT_SAVE_ID,
    COMPONENT_SCOPE_FIELD_ID,
    COMPONENT_SCOPE_ID,
    COMPONENTS_LIST_ID,
    CREATE_BUTTON_ID,
    CREATE_CANCEL_ID,
    CREATE_KIND_ID,
    CREATE_MODAL_ID,
    CREATE_OPEN_ID,
    CREATE_NAME_ID,
    CREATE_RESULT_ID,
    DISPATCH_FRESHNESS_FIELD_ID,
    DRAFT_LOAD_SIGNAL_ID,
    DISPATCH_FRESHNESS_ID,
    IMPORT_RESULT_ID,
    IMPORT_UPLOAD_ID,
    PI_FRESHNESS_FIELD_ID,
    PI_FRESHNESS_ID,
    REFERENCE_ID,
    SAVE_BUTTON_ID,
    SAVE_RESULT_ID,
    SELECTED_TOOL_ID,
    SOURCE_REVISION_STORE_ID,
    SOURCES_ID,
    STRUCTURE_RESULT_ID,
    STRUCTURE_STORE_ID,
    SUBCOMPONENT_CANCEL_ID,
    SUBCOMPONENT_EDITOR_STORE_ID,
    SUBCOMPONENT_LINKED_FIELD_ID,
    SUBCOMPONENT_LINKED_ID,
    SUBCOMPONENT_MODAL_ID,
    SUBCOMPONENT_MODAL_RESULT_ID,
    SUBCOMPONENT_MODAL_TITLE_ID,
    SUBCOMPONENT_NAME_ID,
    SUBCOMPONENT_PARENT_ID,
    SUBCOMPONENT_SAVE_ID,
    SUBCOMPONENTS_LIST_ID,
    TOOL_KEY_ID,
    TOOL_KIND_ID,
    TOOL_NAME_ID,
    TOOL_SCOPE_ID,
    component_delete_id,
    component_edit_id,
    component_move_id,
    subcomponent_delete_id,
    subcomponent_edit_id,
    subcomponent_move_id,
)
from ada.configuration.tools.web.models import ToolAdminWebContext
from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolScope,
    ToolSectionKind,
    ToolSourceKey,
)

_MODAL_CLOSED = 'ada-tools-admin__modal'
_MODAL_OPEN = 'ada-tools-admin__modal ada-tools-admin__modal--open'
_FIELD_VISIBLE = 'ada-tools-admin__modal-field'
_FIELD_HIDDEN = 'ada-tools-admin__modal-field ada-tools-admin__modal-field--hidden'
_SOURCE_VISIBLE = 'ada-tools-admin__source-field'
_SOURCE_HIDDEN = 'ada-tools-admin__source-field ada-tools-admin__source-field--hidden'


def _matches_trigger(trigger: object, *ids: str) -> bool:
    return isinstance(trigger, str) and trigger in ids


def _pattern_click_is_real(
    trigger: object,
    clicks: list[int | None] | None,
    ids: list[dict[str, object]] | None,
) -> bool:
    if not isinstance(trigger, dict):
        return False
    target = dict(trigger)
    for item_id, click_count in zip(ids or [], clicks or [], strict=False):
        if dict(item_id) != target:
            continue
        return (
            isinstance(click_count, int)
            and not isinstance(click_count, bool)
            and click_count > 0
        )
    return False


def register_tool_admin_callbacks(app: object, context: ToolAdminWebContext) -> None:
    @app.callback(
        Output(CATALOG_STORE_ID, 'data', allow_duplicate=True),
        Output(SELECTED_TOOL_ID, 'options', allow_duplicate=True),
        Output(SELECTED_TOOL_ID, 'value', allow_duplicate=True),
        Output(DRAFT_LOAD_SIGNAL_ID, 'data', allow_duplicate=True),
        Input(context.draft_store_id, 'data'),
        State(SELECTED_TOOL_ID, 'value'),
        State(DRAFT_LOAD_SIGNAL_ID, 'data'),
        prevent_initial_call=True,
    )
    def load_browser_draft(
        draft_data: dict[str, object] | None,
        selected_tool: str | None,
        load_signal: int | None,
    ):
        try:
            catalog = _catalog_from_browser_draft(draft_data, context.draft_owner_provider())
        except Exception:
            return no_update, no_update, no_update, no_update
        selected = selected_tool
        if selected is None or not any(tool.tool_key == selected for tool in catalog.tools):
            selected = catalog.tools[0].tool_key if catalog.tools else None
        return (
            catalog.to_document(),
            _tool_options(catalog),
            selected,
            int(load_signal or 0) + 1,
        )

    @app.callback(
        Output(SOURCE_REVISION_STORE_ID, 'data', allow_duplicate=True),
        Input(context.workflow_refresh_signal_id, 'data'),
        prevent_initial_call=True,
    )
    def refresh_source_revision(_signal: object):
        try:
            bundle = context.services.administration.load_source()
        except Exception:
            return no_update
        return bundle.revision if bundle is not None else None

    @app.callback(
        Output(CREATE_MODAL_ID, 'className'),
        Output(SELECTED_TOOL_ID, 'options'),
        Output(SELECTED_TOOL_ID, 'value', allow_duplicate=True),
        Output(CATALOG_STORE_ID, 'data', allow_duplicate=True),
        Output(CREATE_NAME_ID, 'value'),
        Output(CREATE_KIND_ID, 'value'),
        Output(CREATE_RESULT_ID, 'children'),
        Input(CREATE_OPEN_ID, 'n_clicks'),
        Input(CREATE_CANCEL_ID, 'n_clicks'),
        Input(CREATE_CANCEL_ID + '-header', 'n_clicks'),
        Input(CREATE_CANCEL_ID + '-footer', 'n_clicks'),
        Input(CREATE_BUTTON_ID, 'n_clicks'),
        State(CREATE_NAME_ID, 'value'),
        State(CREATE_KIND_ID, 'value'),
        State(CATALOG_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def create_tool(
        _open_clicks: int,
        _cancel_clicks: int,
        _header_cancel_clicks: int,
        _footer_cancel_clicks: int,
        _save_clicks: int,
        display_name: str | None,
        kind_value: str | None,
        catalog_data: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if _matches_trigger(
            trigger,
            CREATE_CANCEL_ID,
            CREATE_CANCEL_ID + '-header',
            CREATE_CANCEL_ID + '-footer',
        ):
            return _MODAL_CLOSED, no_update, no_update, no_update, '', None, ''
        if trigger == CREATE_OPEN_ID:
            return _MODAL_OPEN, no_update, no_update, no_update, '', None, ''
        if trigger != CREATE_BUTTON_ID:
            return _MODAL_CLOSED, no_update, no_update, no_update, no_update, no_update, ''
        if not context.can_manage():
            return (
                _MODAL_OPEN,
                no_update,
                no_update,
                no_update,
                display_name,
                kind_value,
                _error('Management access is denied'),
            )
        try:
            name = (display_name or '').strip()
            key = build_identity_key(name)
            kind = ToolConfigurationKind(str(kind_value or ''))
            catalog = _catalog(catalog_data)
            if any(tool.tool_key == key for tool in catalog.tools):
                raise ValueError('Tool key already exists')
            tool = ToolConfiguration(
                tool_key=key,
                display_name=name,
                kind=kind,
                operational_scope=None,
            )
            updated = catalog.replace(tool)
        except Exception as error:
            return (
                _MODAL_OPEN,
                no_update,
                no_update,
                no_update,
                display_name,
                kind_value,
                _error(str(error)),
            )
        return (
            _MODAL_CLOSED,
            _tool_options(updated),
            key,
            updated.to_document(),
            '',
            None,
            '',
        )

    @app.callback(
        Output(TOOL_NAME_ID, 'value'),
        Output(TOOL_KEY_ID, 'children'),
        Output(APPLICATION_KEY_ID, 'children'),
        Output(TOOL_KIND_ID, 'children'),
        Output(TOOL_SCOPE_ID, 'value'),
        Output(TOOL_SCOPE_ID, 'disabled'),
        Output(SOURCES_ID, 'value'),
        Output(PI_FRESHNESS_ID, 'value'),
        Output(DISPATCH_FRESHNESS_ID, 'value'),
        Input(SELECTED_TOOL_ID, 'value'),
        Input(CATALOG_STORE_ID, 'data'),
    )
    def load_tool(tool_key: str | None, catalog_data: dict[str, object] | None):
        if not tool_key:
            return ('', '', '', '', None, True, [], None, None)
        try:
            tool = _catalog(catalog_data).require(tool_key)
        except Exception:
            return ('', '', '', '', None, True, [], None, None)
        freshness = {source.key: source.stale_after_seconds for source in tool.sources}
        is_integrated = tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS
        return (
            tool.display_name,
            tool.tool_key,
            tool.application_key,
            'Operaciones Integradas' if is_integrated else 'Process',
            'global' if is_integrated else _scope_value(tool.operational_scope),
            is_integrated,
            [source.key.value for source in tool.sources],
            freshness.get(ToolSourceKey.PI),
            freshness.get(ToolSourceKey.DISPATCH),
        )

    @app.callback(
        Output(STRUCTURE_STORE_ID, 'data'),
        Input(SELECTED_TOOL_ID, 'value'),
        Input(DRAFT_LOAD_SIGNAL_ID, 'data'),
        State(CATALOG_STORE_ID, 'data'),
    )
    def load_tool_structure(
        tool_key: str | None,
        _draft_load_signal: int | None,
        catalog_data: dict[str, object] | None,
    ):
        tool = _optional_tool(tool_key, catalog_data)
        if tool is None:
            return []
        return [component.to_document() for component in tool.components]

    @app.callback(
        Output(ADD_SUBCOMPONENT_ID, 'disabled'),
        Input(STRUCTURE_STORE_ID, 'data'),
    )
    def toggle_add_subcomponent(
        structure_data: list[dict[str, object]] | None,
    ) -> bool:
        return not bool(_structure_components(structure_data))

    @app.callback(
        Output(PI_FRESHNESS_FIELD_ID, 'className'),
        Output(DISPATCH_FRESHNESS_FIELD_ID, 'className'),
        Input(SOURCES_ID, 'value'),
    )
    def toggle_source_fields(source_values: list[str] | None):
        selected = set(source_values or [])
        return (
            _SOURCE_VISIBLE if 'pi' in selected else _SOURCE_HIDDEN,
            _SOURCE_VISIBLE if 'dispatch' in selected else _SOURCE_HIDDEN,
        )

    @app.callback(
        Output(COMPONENTS_LIST_ID, 'children'),
        Output(SUBCOMPONENTS_LIST_ID, 'children'),
        Input(STRUCTURE_STORE_ID, 'data'),
        State(SELECTED_TOOL_ID, 'value'),
        State(CATALOG_STORE_ID, 'data'),
    )
    def render_structure(
        structure_data: list[dict[str, object]] | None,
        tool_key: str | None,
        catalog_data: dict[str, object] | None,
    ):
        tool = _optional_tool(tool_key, catalog_data)
        if tool is None:
            empty = _empty_structure('Selecciona o crea una herramienta para comenzar.')
            return empty, empty
        components = _structure_components(structure_data)
        return (
            _render_component_list(tool.kind, components),
            _render_subcomponent_list(tool.kind, components),
        )

    @app.callback(
        Output(COMPONENT_MODAL_ID, 'className'),
        Output(COMPONENT_EDITOR_STORE_ID, 'data'),
        Output(COMPONENT_MODAL_TITLE_ID, 'children'),
        Output(COMPONENT_NAME_ID, 'value'),
        Output(COMPONENT_SCOPE_ID, 'value'),
        Output(COMPONENT_PLACEMENT_ID, 'value'),
        Output(COMPONENT_SCOPE_FIELD_ID, 'className'),
        Output(COMPONENT_PLACEMENT_FIELD_ID, 'className'),
        Output(COMPONENT_MODAL_RESULT_ID, 'children'),
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Output(STRUCTURE_RESULT_ID, 'children', allow_duplicate=True),
        Input(ADD_COMPONENT_ID, 'n_clicks'),
        Input(component_edit_id(ALL), 'n_clicks'),
        Input(COMPONENT_CANCEL_ID, 'n_clicks'),
        Input(COMPONENT_CANCEL_ID + '-header', 'n_clicks'),
        Input(COMPONENT_CANCEL_ID + '-footer', 'n_clicks'),
        Input(COMPONENT_SAVE_ID, 'n_clicks'),
        State(component_edit_id(ALL), 'id'),
        State(COMPONENT_EDITOR_STORE_ID, 'data'),
        State(COMPONENT_NAME_ID, 'value'),
        State(COMPONENT_SCOPE_ID, 'value'),
        State(COMPONENT_PLACEMENT_ID, 'value'),
        State(STRUCTURE_STORE_ID, 'data'),
        State(SELECTED_TOOL_ID, 'value'),
        State(CATALOG_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def component_editor(
        _add_clicks: int,
        _edit_clicks: list[int],
        _cancel_clicks: int,
        _header_cancel_clicks: int,
        _footer_cancel_clicks: int,
        _save_clicks: int,
        edit_ids: list[dict[str, object]],
        editor_data: dict[str, object] | None,
        display_name: str | None,
        scope_value: str | None,
        placement_value: str | None,
        structure_data: list[dict[str, object]] | None,
        tool_key: str | None,
        catalog_data: dict[str, object] | None,
    ):
        tool = _optional_tool(tool_key, catalog_data)
        trigger = ctx.triggered_id
        if tool is None:
            return _component_modal_response(error='Tool selection is required')
        if _matches_trigger(
            trigger,
            COMPONENT_CANCEL_ID,
            COMPONENT_CANCEL_ID + '-header',
            COMPONENT_CANCEL_ID + '-footer',
        ):
            return _component_modal_response(closed=True)
        if trigger == ADD_COMPONENT_ID:
            return _component_modal_response(
                editor={'mode': 'create'},
                title='Nuevo componente',
                scope='mine' if tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS else None,
                scope_visible=tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS,
            )
        if isinstance(trigger, dict) and trigger.get('type') == 'ada-tools-component-edit':
            if not _pattern_click_is_real(trigger, _edit_clicks, edit_ids):
                return _component_modal_response(no_change=True)
            key = str(trigger.get('key', ''))
            component = _require_component(_structure_components(structure_data), key)
            return _component_modal_response(
                editor={'mode': 'edit', 'key': key},
                title='Editar componente',
                name=component.display_name,
                scope=_scope_value(component.scope),
                placement=(
                    component.layout_role.value if component.layout_role is not None else None
                ),
                scope_visible=tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS,
            )
        if trigger != COMPONENT_SAVE_ID:
            return _component_modal_response(closed=True)
        if not context.can_manage():
            return _component_modal_response(
                editor=editor_data,
                name=display_name,
                scope=scope_value,
                placement=placement_value,
                scope_visible=tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS,
                error='Management access is denied',
            )
        try:
            updated = _save_component_draft(
                tool=tool,
                components=_structure_components(structure_data),
                editor_data=editor_data,
                display_name=display_name,
                scope_value=scope_value,
                placement_value=placement_value,
            )
        except Exception as error:
            return _component_modal_response(
                editor=editor_data,
                name=display_name,
                scope=scope_value,
                placement=placement_value,
                scope_visible=tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS,
                error=str(error),
            )
        return _component_modal_response(
            closed=True,
            structure=_structure_document(updated),
            structure_message=None,
        )

    @app.callback(
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Output(STRUCTURE_RESULT_ID, 'children', allow_duplicate=True),
        Input(component_delete_id(ALL), 'n_clicks'),
        State(component_delete_id(ALL), 'id'),
        State(STRUCTURE_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def delete_component(
        _clicks: list[int],
        delete_ids: list[dict[str, object]],
        structure_data: list[dict[str, object]] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, _clicks, delete_ids):
            return no_update, no_update
        key = str(trigger.get('key', ''))
        try:
            components = list(_structure_components(structure_data))
            _ensure_component_is_not_linked(components, key)
            updated = [component for component in components if component.key != key]
        except Exception as error:
            return no_update, _error(str(error))
        return _structure_document(updated), None

    @app.callback(
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Input(component_move_id(ALL, ALL), 'n_clicks'),
        State(component_move_id(ALL, ALL), 'id'),
        State(STRUCTURE_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def move_component(
        _clicks: list[int],
        move_ids: list[dict[str, object]],
        structure_data: list[dict[str, object]] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, _clicks, move_ids):
            return no_update
        updated = _move_item(
            list(_structure_components(structure_data)),
            str(trigger.get('key', '')),
            str(trigger.get('direction', '')),
            key=lambda item: item.key,
        )
        return _structure_document(updated)

    @app.callback(
        Output(SUBCOMPONENT_MODAL_ID, 'className'),
        Output(SUBCOMPONENT_EDITOR_STORE_ID, 'data'),
        Output(SUBCOMPONENT_MODAL_TITLE_ID, 'children'),
        Output(SUBCOMPONENT_PARENT_ID, 'options'),
        Output(SUBCOMPONENT_PARENT_ID, 'value'),
        Output(SUBCOMPONENT_PARENT_ID, 'disabled'),
        Output(SUBCOMPONENT_NAME_ID, 'value'),
        Output(SUBCOMPONENT_LINKED_ID, 'value'),
        Output(SUBCOMPONENT_LINKED_FIELD_ID, 'className'),
        Output(SUBCOMPONENT_MODAL_RESULT_ID, 'children'),
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Output(STRUCTURE_RESULT_ID, 'children', allow_duplicate=True),
        Input(ADD_SUBCOMPONENT_ID, 'n_clicks'),
        Input(subcomponent_edit_id(ALL, ALL), 'n_clicks'),
        Input(SUBCOMPONENT_CANCEL_ID, 'n_clicks'),
        Input(SUBCOMPONENT_CANCEL_ID + '-header', 'n_clicks'),
        Input(SUBCOMPONENT_CANCEL_ID + '-footer', 'n_clicks'),
        Input(SUBCOMPONENT_SAVE_ID, 'n_clicks'),
        State(subcomponent_edit_id(ALL, ALL), 'id'),
        State(SUBCOMPONENT_EDITOR_STORE_ID, 'data'),
        State(SUBCOMPONENT_PARENT_ID, 'value'),
        State(SUBCOMPONENT_NAME_ID, 'value'),
        State(SUBCOMPONENT_LINKED_ID, 'value'),
        State(STRUCTURE_STORE_ID, 'data'),
        State(SELECTED_TOOL_ID, 'value'),
        State(CATALOG_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def subcomponent_editor(
        _add_clicks: int,
        _edit_clicks: list[int],
        _cancel_clicks: int,
        _header_cancel_clicks: int,
        _footer_cancel_clicks: int,
        _save_clicks: int,
        edit_ids: list[dict[str, object]],
        editor_data: dict[str, object] | None,
        parent_key: str | None,
        display_name: str | None,
        linked_keys: list[str] | None,
        structure_data: list[dict[str, object]] | None,
        tool_key: str | None,
        catalog_data: dict[str, object] | None,
    ):
        tool = _optional_tool(tool_key, catalog_data)
        trigger = ctx.triggered_id
        components = list(_structure_components(structure_data))
        if tool is None:
            return _subcomponent_modal_response(error='Tool selection is required')
        options = _component_options(components)
        linked_visible = tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS
        if _matches_trigger(
            trigger,
            SUBCOMPONENT_CANCEL_ID,
            SUBCOMPONENT_CANCEL_ID + '-header',
            SUBCOMPONENT_CANCEL_ID + '-footer',
        ):
            return _subcomponent_modal_response(closed=True)
        if trigger == ADD_SUBCOMPONENT_ID:
            if not components:
                return _subcomponent_modal_response(
                    closed=True,
                    structure_message=_error('Create a component before adding subcomponents'),
                )
            default_parent = components[0].key if len(components) == 1 else None
            return _subcomponent_modal_response(
                editor={'mode': 'create'},
                title='Nuevo subcomponente',
                parent_options=options,
                parent=default_parent,
                linked_visible=linked_visible,
            )
        if isinstance(trigger, dict) and trigger.get('type') == 'ada-tools-subcomponent-edit':
            if not _pattern_click_is_real(trigger, _edit_clicks, edit_ids):
                return _subcomponent_modal_response(no_change=True)
            component_key = str(trigger.get('component', ''))
            key = str(trigger.get('key', ''))
            component = _require_component(components, component_key)
            subcomponent = _require_subcomponent(component, key)
            return _subcomponent_modal_response(
                editor={'mode': 'edit', 'component_key': component_key, 'key': key},
                title='Editar subcomponente',
                parent_options=options,
                parent=component_key,
                parent_disabled=True,
                name=subcomponent.display_name,
                linked=list(subcomponent.linked_component_keys),
                linked_visible=linked_visible,
            )
        if trigger != SUBCOMPONENT_SAVE_ID:
            return _subcomponent_modal_response(closed=True)
        if not context.can_manage():
            return _subcomponent_modal_response(
                editor=editor_data,
                parent_options=options,
                parent=parent_key,
                name=display_name,
                linked=linked_keys,
                linked_visible=linked_visible,
                error='Management access is denied',
            )
        try:
            updated = _save_subcomponent_draft(
                tool=tool,
                components=components,
                editor_data=editor_data,
                parent_key=parent_key,
                display_name=display_name,
                linked_keys=linked_keys or [],
            )
        except Exception as error:
            return _subcomponent_modal_response(
                editor=editor_data,
                parent_options=options,
                parent=parent_key,
                parent_disabled=(editor_data or {}).get('mode') == 'edit',
                name=display_name,
                linked=linked_keys,
                linked_visible=linked_visible,
                error=str(error),
            )
        return _subcomponent_modal_response(
            closed=True,
            structure=_structure_document(updated),
            structure_message=None,
        )

    @app.callback(
        Output(SUBCOMPONENT_LINKED_ID, 'options'),
        Input(SUBCOMPONENT_PARENT_ID, 'value'),
        Input(STRUCTURE_STORE_ID, 'data'),
        State(SELECTED_TOOL_ID, 'value'),
        State(CATALOG_STORE_ID, 'data'),
    )
    def linked_component_options(
        parent_key: str | None,
        structure_data: list[dict[str, object]] | None,
        tool_key: str | None,
        catalog_data: dict[str, object] | None,
    ):
        tool = _optional_tool(tool_key, catalog_data)
        if tool is None or tool.kind is not ToolConfigurationKind.INTEGRATED_OPERATIONS:
            return []
        components = _structure_components(structure_data)
        parent = next((item for item in components if item.key == parent_key), None)
        if parent is None:
            return []
        return [
            {'label': item.display_name, 'value': item.key}
            for item in components
            if item.key != parent.key and item.scope is parent.scope
        ]

    @app.callback(
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Output(STRUCTURE_RESULT_ID, 'children', allow_duplicate=True),
        Input(subcomponent_delete_id(ALL, ALL), 'n_clicks'),
        State(subcomponent_delete_id(ALL, ALL), 'id'),
        State(STRUCTURE_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def delete_subcomponent(
        _clicks: list[int],
        delete_ids: list[dict[str, object]],
        structure_data: list[dict[str, object]] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, _clicks, delete_ids):
            return no_update, no_update
        component_key = str(trigger.get('component', ''))
        key = str(trigger.get('key', ''))
        components = list(_structure_components(structure_data))
        try:
            component = _require_component(components, component_key)
        except Exception as error:
            return no_update, _error(str(error))
        replacement = ToolComponentConfiguration(
            key=component.key,
            display_name=component.display_name,
            scope=component.scope,
            layout_role=component.layout_role,
            subcomponents=tuple(item for item in component.subcomponents if item.key != key),
        )
        return (
            _structure_document(_replace_component(components, replacement)),
            None,
        )

    @app.callback(
        Output(STRUCTURE_STORE_ID, 'data', allow_duplicate=True),
        Input(subcomponent_move_id(ALL, ALL, ALL), 'n_clicks'),
        State(subcomponent_move_id(ALL, ALL, ALL), 'id'),
        State(STRUCTURE_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def move_subcomponent(
        _clicks: list[int],
        move_ids: list[dict[str, object]],
        structure_data: list[dict[str, object]] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, _clicks, move_ids):
            return no_update
        component_key = str(trigger.get('component', ''))
        key = str(trigger.get('key', ''))
        direction = str(trigger.get('direction', ''))
        components = list(_structure_components(structure_data))
        component = _require_component(components, component_key)
        moved = _move_item(
            list(component.subcomponents),
            key,
            direction,
            key=lambda item: item.key,
        )
        replacement = ToolComponentConfiguration(
            key=component.key,
            display_name=component.display_name,
            scope=component.scope,
            layout_role=component.layout_role,
            subcomponents=tuple(moved),
        )
        return _structure_document(_replace_component(components, replacement))

    @app.callback(
        Output(REFERENCE_ID, 'children'),
        Input(SELECTED_TOOL_ID, 'value'),
        Input(TOOL_NAME_ID, 'value'),
        Input(TOOL_SCOPE_ID, 'value'),
        Input(SOURCES_ID, 'value'),
        Input(PI_FRESHNESS_ID, 'value'),
        Input(DISPATCH_FRESHNESS_ID, 'value'),
        Input(STRUCTURE_STORE_ID, 'data'),
        State(CATALOG_STORE_ID, 'data'),
    )
    def render_reference(
        tool_key: str | None,
        display_name: str | None,
        operational_scope: str | None,
        source_values: list[str] | None,
        pi_freshness: int | None,
        dispatch_freshness: int | None,
        structure_data: list[dict[str, object]] | None,
        catalog_data: dict[str, object] | None,
    ):
        current = _optional_tool(tool_key, catalog_data)
        if current is None:
            return _empty_structure('No hay una herramienta seleccionada.')
        try:
            draft = _build_tool_from_editor(
                current=current,
                display_name=str(display_name or ''),
                operational_scope=operational_scope,
                source_values=source_values or [],
                pi_freshness=pi_freshness,
                dispatch_freshness=dispatch_freshness,
                components=_structure_components(structure_data),
            )
        except Exception:
            draft = current
        return _reference_preview(draft)

    @app.callback(
        Output(context.draft_store_id, 'data', allow_duplicate=True),
        Output(IMPORT_RESULT_ID, 'children'),
        Input(IMPORT_UPLOAD_ID, 'contents'),
        State(SOURCE_REVISION_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def import_configuration(
        contents: str | None,
        source_revision: str | None,
    ):
        if contents is None:
            return no_update, no_update
        if not context.can_manage():
            return no_update, _error('Management access is denied')
        try:
            if ',' not in contents:
                raise ValueError('Configuration file payload is invalid')
            payload = base64.b64decode(contents.split(',', 1)[1], validate=True)
            catalog = decode_tool_configuration_import(payload)
            draft = _browser_draft_document(
                catalog=catalog,
                owner_subject_id=context.draft_owner_provider(),
                base_source_revision=source_revision,
            )
        except Exception as error:
            return no_update, _error(str(error))
        return draft, _success('Archivo cargado como borrador local.')

    @app.callback(
        Output(CATALOG_STORE_ID, 'data', allow_duplicate=True),
        Output(SELECTED_TOOL_ID, 'options', allow_duplicate=True),
        Output(SAVE_RESULT_ID, 'children'),
        Output(context.draft_store_id, 'data', allow_duplicate=True),
        Input(SAVE_BUTTON_ID, 'n_clicks'),
        Input(context.draft_save_action_id, 'n_clicks'),
        State(SELECTED_TOOL_ID, 'value'),
        State(TOOL_NAME_ID, 'value'),
        State(TOOL_SCOPE_ID, 'value'),
        State(SOURCES_ID, 'value'),
        State(PI_FRESHNESS_ID, 'value'),
        State(DISPATCH_FRESHNESS_ID, 'value'),
        State(STRUCTURE_STORE_ID, 'data'),
        State(CATALOG_STORE_ID, 'data'),
        State(SOURCE_REVISION_STORE_ID, 'data'),
        State(context.draft_store_id, 'data'),
        prevent_initial_call=True,
    )
    def save_tool_draft(
        content_clicks: int,
        workflow_clicks: int,
        tool_key: str | None,
        display_name: str | None,
        operational_scope: str | None,
        source_values: list[str] | None,
        pi_freshness: int | None,
        dispatch_freshness: int | None,
        structure_data: list[dict[str, object]] | None,
        catalog_data: dict[str, object] | None,
        source_revision: str | None,
        current_draft: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if not _save_draft_click_is_real(
            trigger,
            content_clicks=content_clicks,
            workflow_clicks=workflow_clicks,
            workflow_id=context.draft_save_action_id,
        ):
            return no_update, no_update, no_update, no_update
        if not context.can_manage():
            return no_update, no_update, _error('Management access is denied'), no_update
        try:
            catalog = _catalog(catalog_data)
            current = catalog.require(str(tool_key or ''))
            tool = _build_tool_from_editor(
                current=current,
                display_name=str(display_name or ''),
                operational_scope=operational_scope,
                source_values=source_values or [],
                pi_freshness=pi_freshness,
                dispatch_freshness=dispatch_freshness,
                components=_structure_components(structure_data),
            )
            updated = catalog.replace(tool)
            base_revision = _draft_base_source_revision(
                current_draft,
                owner_subject_id=context.draft_owner_provider(),
                fallback=source_revision,
            )
            draft = _browser_draft_document(
                catalog=updated,
                owner_subject_id=context.draft_owner_provider(),
                base_source_revision=base_revision,
            )
        except Exception as error:
            return no_update, no_update, _error(str(error)), no_update
        return (
            updated.to_document(),
            _tool_options(updated),
            None,
            draft,
        )


def _catalog_from_browser_draft(
    data: dict[str, object] | None,
    owner_subject_id: str,
) -> ToolConfigurationCatalog:
    if not isinstance(data, dict):
        raise ValueError('Browser draft does not exist')
    if data.get('schema_version') != 1:
        raise ValueError('Browser draft schema is invalid')
    if str(data.get('owner_subject_id', '')).strip() != owner_subject_id.strip():
        raise ValueError('Browser draft belongs to another user')
    payload = data.get('payload')
    if not isinstance(payload, dict):
        raise ValueError('Browser draft payload is invalid')
    catalog = ToolConfigurationCatalog.from_document(dict(payload))
    revision = build_tool_configuration_digest(catalog)
    if str(data.get('revision', '')).strip() != revision:
        raise ValueError('Browser draft revision does not match content')
    return catalog


def _browser_draft_document(
    *,
    catalog: ToolConfigurationCatalog,
    owner_subject_id: str,
    base_source_revision: str | None,
) -> dict[str, object]:
    owner = owner_subject_id.strip()
    if not owner:
        raise ValueError('Browser draft owner is required')
    revision = build_tool_configuration_digest(catalog)
    return {
        'schema_version': 1,
        'owner_subject_id': owner,
        'revision': revision,
        'saved_at': datetime.now(UTC).isoformat(),
        'base_source_revision': base_source_revision,
        'payload': catalog.to_document(),
    }


def _draft_base_source_revision(
    data: dict[str, object] | None,
    *,
    owner_subject_id: str,
    fallback: str | None,
) -> str | None:
    if not isinstance(data, dict):
        return fallback
    if str(data.get('owner_subject_id', '')).strip() != owner_subject_id.strip():
        return fallback
    value = data.get('base_source_revision')
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _save_draft_click_is_real(
    trigger: object,
    *,
    content_clicks: int | None,
    workflow_clicks: int | None,
    workflow_id: object,
) -> bool:
    if trigger == SAVE_BUTTON_ID:
        return _click_is_real(content_clicks)
    if isinstance(trigger, dict) and isinstance(workflow_id, dict):
        if dict(trigger) == dict(workflow_id):
            return _click_is_real(workflow_clicks)
    return False


def _click_is_real(clicks: int | None) -> bool:
    return isinstance(clicks, int) and not isinstance(clicks, bool) and clicks > 0

def _catalog(data: dict[str, object] | None) -> ToolConfigurationCatalog:
    if not isinstance(data, dict):
        return ToolConfigurationCatalog(())
    return ToolConfigurationCatalog.from_document(data)


def _optional_tool(
    tool_key: str | None,
    catalog_data: dict[str, object] | None,
) -> ToolConfiguration | None:
    if not tool_key:
        return None
    try:
        return _catalog(catalog_data).require(tool_key)
    except Exception:
        return None


def _tool_options(catalog: ToolConfigurationCatalog) -> list[dict[str, str]]:
    return [
        {'label': item.display_name, 'value': item.tool_key}
        for item in catalog.tools
    ]


def _scope_value(scope: ToolScope | None) -> str | None:
    return scope.value if scope is not None else None


def _structure_components(
    data: list[dict[str, object]] | None,
) -> tuple[ToolComponentConfiguration, ...]:
    if not isinstance(data, list):
        return ()
    return tuple(
        ToolComponentConfiguration.from_document(item)
        for item in data
        if isinstance(item, dict)
    )


def _structure_document(
    components: list[ToolComponentConfiguration] | tuple[ToolComponentConfiguration, ...],
) -> list[dict[str, object]]:
    return [component.to_document() for component in components]


def _render_component_list(
    kind: ToolConfigurationKind,
    components: tuple[ToolComponentConfiguration, ...],
) -> object:
    if not components:
        return _empty_structure('Aún no hay componentes. Usa “+ Componente” para crear el primero.')
    cards = []
    for index, component in enumerate(components):
        detail = (
            _scope_label(component.scope)
            if kind is ToolConfigurationKind.INTEGRATED_OPERATIONS
            else _placement_label(component.layout_role)
        )
        cards.append(
            html.Article(
                [
                    html.Div(
                        [
                            html.Strong(component.display_name),
                            html.Code(component.key),
                            html.Span(
                                f'{detail} · {len(component.subcomponents)} subcomponentes'
                            ),
                        ],
                        className='ada-tools-admin__structure-copy',
                    ),
                    _component_actions(component.key, index, len(components)),
                ],
                className='ada-tools-admin__structure-card',
            )
        )
    return cards


def _render_subcomponent_list(
    kind: ToolConfigurationKind,
    components: tuple[ToolComponentConfiguration, ...],
) -> object:
    rows = []
    for component in components:
        for index, subcomponent in enumerate(component.subcomponents):
            linked = ''
            if kind is ToolConfigurationKind.INTEGRATED_OPERATIONS:
                names = [
                    _require_component(components, key).display_name
                    for key in subcomponent.linked_component_keys
                ]
                linked = f' · Compartido con: {", ".join(names)}' if names else ''
            rows.append(
                html.Article(
                    [
                        html.Div(
                            [
                                html.Strong(subcomponent.display_name),
                                html.Code(f'{component.key}_{subcomponent.key}'),
                                html.Span(f'Componente: {component.display_name}{linked}'),
                            ],
                            className='ada-tools-admin__structure-copy',
                        ),
                        _subcomponent_actions(
                            component.key,
                            subcomponent.key,
                            index,
                            len(component.subcomponents),
                        ),
                    ],
                    className='ada-tools-admin__structure-card',
                )
            )
    if not rows:
        return _empty_structure(
            'Aún no hay subcomponentes. Cada componente debe incorporar los que corresponda.'
        )
    return rows


def _component_actions(key: str, index: int, total: int) -> object:
    return html.Div(
        [
            html.Button(
                '↑',
                id=component_move_id(key, 'up'),
                n_clicks=0,
                disabled=index == 0,
                className='ada-tools-admin__structure-icon',
                title='Subir componente',
            ),
            html.Button(
                '↓',
                id=component_move_id(key, 'down'),
                n_clicks=0,
                disabled=index == total - 1,
                className='ada-tools-admin__structure-icon',
                title='Bajar componente',
            ),
            html.Button(
                'Editar',
                id=component_edit_id(key),
                n_clicks=0,
                className='ada-tools-admin__structure-action',
            ),
            html.Button(
                'Eliminar',
                id=component_delete_id(key),
                n_clicks=0,
                className=(
                    'ada-tools-admin__structure-action '
                    'ada-tools-admin__structure-action--danger'
                ),
            ),
        ],
        className='ada-tools-admin__structure-actions',
    )


def _subcomponent_actions(
    component_key: str,
    key: str,
    index: int,
    total: int,
) -> object:
    return html.Div(
        [
            html.Button(
                '↑',
                id=subcomponent_move_id(component_key, key, 'up'),
                n_clicks=0,
                disabled=index == 0,
                className='ada-tools-admin__structure-icon',
                title='Subir subcomponente',
            ),
            html.Button(
                '↓',
                id=subcomponent_move_id(component_key, key, 'down'),
                n_clicks=0,
                disabled=index == total - 1,
                className='ada-tools-admin__structure-icon',
                title='Bajar subcomponente',
            ),
            html.Button(
                'Editar',
                id=subcomponent_edit_id(component_key, key),
                n_clicks=0,
                className='ada-tools-admin__structure-action',
            ),
            html.Button(
                'Eliminar',
                id=subcomponent_delete_id(component_key, key),
                n_clicks=0,
                className=(
                    'ada-tools-admin__structure-action '
                    'ada-tools-admin__structure-action--danger'
                ),
            ),
        ],
        className='ada-tools-admin__structure-actions',
    )


def _save_component_draft(
    *,
    tool: ToolConfiguration,
    components: tuple[ToolComponentConfiguration, ...],
    editor_data: dict[str, object] | None,
    display_name: str | None,
    scope_value: str | None,
    placement_value: str | None,
) -> list[ToolComponentConfiguration]:
    name = str(display_name or '').strip()
    mode = str((editor_data or {}).get('mode', ''))
    if mode not in {'create', 'edit'}:
        raise ValueError('Component editor state is invalid')
    if not name:
        raise ValueError('Component name is required')
    if mode == 'edit':
        key = str((editor_data or {}).get('key', ''))
        current = _require_component(components, key)
        subcomponents = current.subcomponents
    else:
        key = build_identity_key(name)
        if any(item.key == key for item in components):
            raise ValueError('Component key already exists')
        subcomponents = ()
    if tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS:
        if scope_value not in {'mine', 'plant'}:
            raise ValueError('Integrated operations component area is required')
        replacement = ToolComponentConfiguration(
            key=key,
            display_name=name,
            scope=ToolScope(scope_value),
            subcomponents=subcomponents,
        )
    else:
        if placement_value not in {'left', 'center', 'right', 'bottom'}:
            raise ValueError('Process component placement is required')
        placement = ProcessBodySection(placement_value)
        if any(
            item.key != key and item.layout_role is placement
            for item in components
        ):
            raise ValueError('Process component placement must be unique')
        replacement = ToolComponentConfiguration(
            key=key,
            display_name=name,
            layout_role=placement,
            subcomponents=subcomponents,
        )
    updated = _replace_component(list(components), replacement)
    if tool.kind is ToolConfigurationKind.INTEGRATED_OPERATIONS:
        _validate_shared_component_scopes(updated)
    return updated


def _save_subcomponent_draft(
    *,
    tool: ToolConfiguration,
    components: list[ToolComponentConfiguration],
    editor_data: dict[str, object] | None,
    parent_key: str | None,
    display_name: str | None,
    linked_keys: list[str],
) -> list[ToolComponentConfiguration]:
    name = str(display_name or '').strip()
    mode = str((editor_data or {}).get('mode', ''))
    if mode not in {'create', 'edit'}:
        raise ValueError('Subcomponent editor state is invalid')
    if not name:
        raise ValueError('Subcomponent name is required')
    if not parent_key:
        raise ValueError('Subcomponent component is required')
    parent = _require_component(components, parent_key)
    if mode == 'edit':
        original_parent = str((editor_data or {}).get('component_key', ''))
        key = str((editor_data or {}).get('key', ''))
        if parent_key != original_parent:
            raise ValueError('Existing subcomponent parent cannot be changed')
        _require_subcomponent(parent, key)
    else:
        key = build_identity_key(name)
        if any(item.key == key for item in parent.subcomponents):
            raise ValueError('Subcomponent key already exists in the selected component')
    linked = _validate_linked_components(tool, components, parent, linked_keys)
    replacement = ToolSubcomponentConfiguration(
        key=key,
        display_name=name,
        linked_component_keys=linked,
    )
    subcomponents = list(parent.subcomponents)
    position = next((index for index, item in enumerate(subcomponents) if item.key == key), None)
    if position is None:
        subcomponents.append(replacement)
    else:
        subcomponents[position] = replacement
    parent_replacement = ToolComponentConfiguration(
        key=parent.key,
        display_name=parent.display_name,
        scope=parent.scope,
        layout_role=parent.layout_role,
        subcomponents=tuple(subcomponents),
    )
    return _replace_component(components, parent_replacement)


def _validate_shared_component_scopes(
    components: list[ToolComponentConfiguration],
) -> None:
    by_key = {component.key: component for component in components}
    for component in components:
        for subcomponent in component.subcomponents:
            for linked_key in subcomponent.linked_component_keys:
                linked = by_key.get(linked_key)
                if linked is None:
                    raise ValueError('Shared subcomponent references an unknown component')
                if linked.scope is not component.scope:
                    raise ValueError(
                        'Shared subcomponents must link components from the same area'
                    )


def _validate_linked_components(
    tool: ToolConfiguration,
    components: list[ToolComponentConfiguration],
    parent: ToolComponentConfiguration,
    linked_keys: list[str],
) -> tuple[str, ...]:
    if tool.kind is ToolConfigurationKind.PROCESS:
        return ()
    linked = tuple(dict.fromkeys(str(value) for value in linked_keys if str(value)))
    for key in linked:
        component = _require_component(components, key)
        if component.key == parent.key:
            raise ValueError('Subcomponent cannot be linked to its parent component')
        if component.scope is not parent.scope:
            raise ValueError('Shared subcomponents must link components from the same area')
    return linked


def _replace_component(
    components: list[ToolComponentConfiguration],
    replacement: ToolComponentConfiguration,
) -> list[ToolComponentConfiguration]:
    for index, component in enumerate(components):
        if component.key == replacement.key:
            components[index] = replacement
            return components
    components.append(replacement)
    return components


def _ensure_component_is_not_linked(
    components: list[ToolComponentConfiguration],
    key: str,
) -> None:
    for component in components:
        for subcomponent in component.subcomponents:
            if key in subcomponent.linked_component_keys:
                raise ValueError('Component is referenced by a shared subcomponent')


def _require_component(
    components: list[ToolComponentConfiguration] | tuple[ToolComponentConfiguration, ...],
    key: str,
) -> ToolComponentConfiguration:
    for component in components:
        if component.key == key:
            return component
    raise ValueError('Component could not be found')


def _require_subcomponent(
    component: ToolComponentConfiguration,
    key: str,
) -> ToolSubcomponentConfiguration:
    for subcomponent in component.subcomponents:
        if subcomponent.key == key:
            return subcomponent
    raise ValueError('Subcomponent could not be found')


def _move_item(items: list[object], item_key: str, direction: str, *, key) -> list[object]:
    index = next((position for position, item in enumerate(items) if key(item) == item_key), None)
    if index is None:
        return items
    target = index - 1 if direction == 'up' else index + 1
    if target < 0 or target >= len(items):
        return items
    items[index], items[target] = items[target], items[index]
    return items


def _component_options(
    components: list[ToolComponentConfiguration],
) -> list[dict[str, str]]:
    return [
        {'label': component.display_name, 'value': component.key}
        for component in components
    ]


def _build_tool_from_editor(
    *,
    current: ToolConfiguration,
    display_name: str,
    operational_scope: str | None,
    source_values: list[str],
    pi_freshness: int | None,
    dispatch_freshness: int | None,
    components: tuple[ToolComponentConfiguration, ...],
) -> ToolConfiguration:
    sources = []
    selected = set(source_values)
    if 'pi' in selected:
        sources.append(
            ToolSourceConfiguration(
                ToolSourceKey.PI,
                stale_after_seconds=int(pi_freshness or 0),
            )
        )
    if 'dispatch' in selected:
        sources.append(
            ToolSourceConfiguration(
                ToolSourceKey.DISPATCH,
                stale_after_seconds=int(dispatch_freshness or 0),
            )
        )
    return ToolConfiguration(
        tool_key=current.tool_key,
        display_name=display_name,
        kind=current.kind,
        operational_scope=(
            ToolScope(operational_scope)
            if current.kind is ToolConfigurationKind.PROCESS and operational_scope
            else None
        ),
        sources=tuple(sources),
        components=components,
    )


def _reference_preview(tool: ToolConfiguration) -> object:
    summary = html.Div(
        [
            _reference_item('Tool ID', tool.tool_key),
            _reference_item('Aplicación', tool.application_key),
            _reference_item('Componentes', str(len(tool.components))),
            _reference_item(
                'Subcomponentes',
                str(sum(len(component.subcomponents) for component in tool.components)),
            ),
        ],
        className='ada-tools-admin__reference-grid',
    )
    try:
        manifest = build_tool_manifest(tool)
    except Exception:
        runtime = html.P(
            (
                'La vista runtime estará disponible cuando el borrador cumpla '
                'las reglas de proyección.'
            ),
            className='ada-tools-admin__reference-help',
        )
    else:
        rows = []
        for section in manifest.sections:
            if section.kind is ToolSectionKind.REGION:
                continue
            targets = ', '.join(sorted(target.value.upper() for target in section.targets)) or '—'
            layout = section.layout_role.value if section.layout_role is not None else '—'
            rows.append(
                html.Tr(
                    [
                        html.Td(section.display_name),
                        html.Td(html.Code(section.key)),
                        html.Td(section.scope.value),
                        html.Td(layout),
                        html.Td(targets),
                    ]
                )
            )
        runtime = html.Div(
            [
                html.P(
                    'Vista derivada; estos valores no son editables.',
                    className='ada-tools-admin__reference-help',
                ),
                html.Div(
                    html.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th('Sección'),
                                        html.Th('ID runtime'),
                                        html.Th('Scope'),
                                        html.Th('Ubicación'),
                                        html.Th('Targets'),
                                    ]
                                )
                            ),
                            html.Tbody(rows),
                        ]
                    ),
                    className='ada-tools-admin__reference-table-wrap',
                ),
            ]
        )
    return html.Div(
        [
            html.H3('Referencia generada'),
            html.P(
                'ADA deriva estos datos automáticamente a partir de la configuración.',
                className='ada-tools-admin__reference-help',
            ),
            summary,
            html.Details(
                [html.Summary('Ver manifest runtime generado'), runtime],
                className='ada-tools-admin__runtime-preview',
            ),
        ],
        className='ada-tools-admin__reference',
    )


def _component_modal_response(
    *,
    no_change: bool = False,
    closed: bool = False,
    editor: dict[str, object] | None = None,
    title: str | None = None,
    name: str | None = None,
    scope: str | None = None,
    placement: str | None = None,
    scope_visible: bool = True,
    error: str | None = None,
    structure: list[dict[str, object]] | object = no_update,
    structure_message: object = no_update,
) -> tuple[object, ...]:
    if no_change:
        return (no_update,) * 11
    if closed:
        return (
            _MODAL_CLOSED,
            None,
            '',
            '',
            None,
            None,
            _FIELD_VISIBLE,
            _FIELD_HIDDEN,
            None,
            structure,
            structure_message,
        )
    return (
        _MODAL_OPEN,
        editor,
        title or 'Componente',
        name or '',
        scope,
        placement,
        _FIELD_VISIBLE if scope_visible else _FIELD_HIDDEN,
        _FIELD_HIDDEN if scope_visible else _FIELD_VISIBLE,
        _error(error) if error else None,
        structure,
        structure_message,
    )


def _subcomponent_modal_response(
    *,
    no_change: bool = False,
    closed: bool = False,
    editor: dict[str, object] | None = None,
    title: str | None = None,
    parent_options: list[dict[str, str]] | None = None,
    parent: str | None = None,
    parent_disabled: bool = False,
    name: str | None = None,
    linked: list[str] | None = None,
    linked_visible: bool = True,
    error: str | None = None,
    structure: list[dict[str, object]] | object = no_update,
    structure_message: object = no_update,
) -> tuple[object, ...]:
    if no_change:
        return (no_update,) * 12
    if closed:
        return (
            _MODAL_CLOSED,
            None,
            '',
            [],
            None,
            False,
            '',
            [],
            _FIELD_VISIBLE,
            None,
            structure,
            structure_message,
        )
    return (
        _MODAL_OPEN,
        editor,
        title or 'Subcomponente',
        parent_options or [],
        parent,
        parent_disabled,
        name or '',
        linked or [],
        _FIELD_VISIBLE if linked_visible else _FIELD_HIDDEN,
        _error(error) if error else None,
        structure,
        structure_message,
    )


def _scope_label(scope: ToolScope | None) -> str:
    return {
        ToolScope.MINE: 'Mina',
        ToolScope.PLANT: 'Planta',
    }.get(scope, 'Sin área')


def _placement_label(placement: ProcessBodySection | None) -> str:
    return {
        ProcessBodySection.CENTER: 'Proceso principal',
        ProcessBodySection.LEFT: 'Aguas arriba',
        ProcessBodySection.RIGHT: 'Aguas abajo',
        ProcessBodySection.BOTTOM: 'Inferior / especial',
    }.get(placement, 'Sin ubicación')


def _reference_item(label: str, value: str) -> object:
    return html.Div([html.Span(label), html.Code(value)])


def _empty_structure(message: str) -> object:
    return html.Div(message, className='ada-tools-admin__empty')


def _success(message: str) -> object:
    return html.Div(message, className='ada-tools-admin__message--success')


def _error(message: str) -> object:
    return html.Div(message, className='ada-tools-admin__message ada-tools-admin__message--error')
