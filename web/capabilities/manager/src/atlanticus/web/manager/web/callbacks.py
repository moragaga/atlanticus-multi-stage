from __future__ import annotations

from dash import ALL, MATCH, Input, Output, State, ctx, no_update

from atlanticus.web.manager.authorization import ManagerAuthorizationPolicy
from atlanticus.web.manager.coordinator import ManagerProjectionCoordinator
from atlanticus.web.manager.errors import ManagerError, ManagerProjectionError
from atlanticus.web.manager.models import ManagerPrincipal, ManagerSurfaceDefinition
from atlanticus.web.manager.projection import (
    ManagerDraft,
    ProjectionIssue,
    ProjectionState,
    ProjectionStatus,
    resolve_projection_state,
)
from atlanticus.web.manager.registry import ManagerModuleRegistry
from atlanticus.web.manager.web.ids import (
    CONTENT_ID,
    LOCATION_ID,
    REFRESH_SIGNAL_ID,
    SIDEBAR_BACKDROP_ID,
    SIDEBAR_CLOSE_ID,
    SIDEBAR_ID,
    SIDEBAR_MODULES_ID,
    SIDEBAR_TOGGLE_ID,
    STATUS_STORE_ID,
    SUMMARY_ID,
    history_load_id,
    module_section_button_id,
    module_section_panel_id,
    module_section_store_id,
    module_status_id,
    workflow_action_id,
    workflow_draft_id,
    workflow_draft_status_id,
    workflow_history_id,
    workflow_projection_signal_id,
    workflow_refresh_signal_id,
    workflow_result_id,
    workflow_revision_id,
    workflow_status_id,
    workflow_validation_id,
)
from atlanticus.web.manager.web.layout import (
    build_module_content,
    build_sidebar_modules,
    build_summary,
    build_workflow_draft_content,
    build_workflow_history_content,
    build_workflow_status_content,
)
from atlanticus.web.services import ServiceRegistry


def register_manager_callbacks(
    app: object,
    *,
    definition: ManagerSurfaceDefinition,
    registry: ManagerModuleRegistry,
    services: ServiceRegistry,
    authorization: ManagerAuthorizationPolicy,
) -> None:
    coordinator = ManagerProjectionCoordinator(
        registry=registry,
        services=services,
        authorization=authorization,
    )
    source_inputs = [
        Input(module.source_signal_id, 'data')
        for module in registry.modules
        if module.source_signal_id is not None
    ]

    @app.callback(
        Output(SIDEBAR_ID, 'className'),
        Output(SIDEBAR_BACKDROP_ID, 'className'),
        Input(SIDEBAR_TOGGLE_ID, 'n_clicks'),
        Input(SIDEBAR_CLOSE_ID, 'n_clicks'),
        Input(SIDEBAR_BACKDROP_ID, 'n_clicks'),
        Input(LOCATION_ID, 'pathname'),
        prevent_initial_call=True,
    )
    def toggle_sidebar(_open: int, _close: int, _backdrop: int, _pathname: str):
        trigger = ctx.triggered_id
        if trigger == SIDEBAR_TOGGLE_ID:
            return (
                'atlanticus-manager__sidebar atlanticus-manager__sidebar--open',
                'atlanticus-manager__sidebar-backdrop atlanticus-manager__sidebar-backdrop--open',
            )
        return 'atlanticus-manager__sidebar', 'atlanticus-manager__sidebar-backdrop'

    @app.callback(
        Output(STATUS_STORE_ID, 'data'),
        Output(SUMMARY_ID, 'children'),
        Input(REFRESH_SIGNAL_ID, 'data'),
        Input(workflow_refresh_signal_id(ALL), 'data'),
        *source_inputs,
    )
    def refresh_statuses(_refresh_clicks: int, _workflow_signals: list[object], *_signals: object):
        principal = definition.principal_provider()
        states: dict[str, str] = {}
        for module in registry.visible_modules(principal, authorization):
            try:
                state = resolve_projection_state(coordinator.get_status(module.key, principal))
            except Exception:
                state = ProjectionState.UNAVAILABLE
            states[module.key] = state.value
        resolved_states = {key: ProjectionState(value) for key, value in states.items()}
        return states, build_summary(resolved_states)

    @app.callback(
        Output(workflow_validation_id(ALL), 'data', allow_duplicate=True),
        Input(REFRESH_SIGNAL_ID, 'data'),
        prevent_initial_call=True,
    )
    def clear_transient_validation(clicks: int):
        if not _click_is_real(clicks):
            return no_update
        principal = definition.principal_provider()
        visible_modules = registry.visible_modules(principal, authorization)
        return [None for _ in visible_modules]

    @app.callback(
        Output(SIDEBAR_MODULES_ID, 'children'),
        Input(STATUS_STORE_ID, 'data'),
        Input(LOCATION_ID, 'pathname'),
    )
    def render_sidebar(states_data: dict[str, str] | None, pathname: str | None):
        principal = definition.principal_provider()
        states = {key: _safe_state(value) for key, value in (states_data or {}).items()}
        return build_sidebar_modules(
            registry=registry,
            modules=registry.visible_modules(principal, authorization),
            current_path=(
                pathname
                or registry.route_for(registry.require(definition.default_module_key))
            ),
            states=states,
        )

    @app.callback(
        Output(CONTENT_ID, 'children'),
        Input(LOCATION_ID, 'pathname'),
    )
    def render_content(pathname: str | None):
        principal = definition.principal_provider()
        module = _active_module(registry, definition, pathname)
        if module is None or not authorization.can_view(principal, module):
            from dash import html

            return html.Div(
                'Configuration module was not found',
                className='atlanticus-manager__message atlanticus-manager__message--error',
            )
        return build_module_content(
            module=module,
            services=services,
            coordinator=coordinator,
            principal=principal,
        )

    @app.callback(
        Output(module_section_store_id(MATCH), 'data'),
        Input(module_section_button_id(MATCH, ALL), 'n_clicks'),
        State(module_section_button_id(MATCH, ALL), 'id'),
        State(module_section_store_id(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def select_section(
        clicks: list[int],
        button_ids: list[dict[str, object]],
        current: str,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, clicks, button_ids):
            return current
        return str(trigger.get('section', current))

    @app.callback(
        Output(module_section_panel_id(MATCH, 'content'), 'className'),
        Output(module_section_panel_id(MATCH, 'workflow'), 'className'),
        Output(module_section_button_id(MATCH, 'content'), 'className'),
        Output(module_section_button_id(MATCH, 'workflow'), 'className'),
        Input(module_section_store_id(MATCH), 'data'),
    )
    def render_section(section: str):
        content_active = section == 'content'
        workflow_active = section == 'workflow'
        return (
            _panel_class(content_active),
            _panel_class(workflow_active),
            _tab_class(content_active),
            _tab_class(workflow_active),
        )

    @app.callback(
        Output(workflow_status_id(ALL), 'children'),
        Output(workflow_history_id(ALL), 'children'),
        Output(workflow_revision_id(ALL), 'data'),
        Output(workflow_action_id(ALL, 'project'), 'disabled'),
        Output(module_status_id(ALL), 'children'),
        Output(module_status_id(ALL), 'className'),
        Input(STATUS_STORE_ID, 'data'),
        Input(LOCATION_ID, 'pathname'),
    )
    def refresh_active_workflow(
        _status_data: dict[str, str] | None,
        pathname: str | None,
    ):
        principal = definition.principal_provider()
        module = _active_module(registry, definition, pathname)
        if module is None or not authorization.can_view(principal, module):
            return [], [], [], [], [], []
        status, history, can_load_history, status_error = _load_workflow_state(
            coordinator,
            module.key,
            principal,
        )
        state = (
            resolve_projection_state(status) if status is not None else ProjectionState.UNAVAILABLE
        )
        return (
            [
                build_workflow_status_content(
                    module=module,
                    status=status,
                    error=status_error,
                )
            ],
            [
                build_workflow_history_content(
                    module=module,
                    status=status,
                    history=history,
                    can_load_history=can_load_history,
                    error=status_error,
                )
            ],
            [_workflow_revision_state(status)],
            [not _can_project(status)],
            [_state_label(state)],
            [_state_class(state)],
        )

    @app.callback(
        Output(workflow_draft_status_id(MATCH), 'children'),
        Output(workflow_action_id(MATCH, 'validate'), 'disabled'),
        Output(workflow_action_id(MATCH, 'publish'), 'disabled'),
        Input(workflow_draft_id(MATCH), 'data'),
        Input(workflow_validation_id(MATCH), 'data'),
        Input(workflow_revision_id(MATCH), 'data'),
    )
    def refresh_draft_workflow(
        draft_data: dict[str, object] | None,
        validation_data: dict[str, object] | None,
        revision_state: dict[str, object] | None,
    ):
        principal = definition.principal_provider()
        draft = _safe_draft(draft_data, principal)
        source_revision = _source_revision(revision_state)
        validation_current = _validation_is_current(draft, validation_data)
        publication_pending = bool(draft is not None and draft.revision != source_revision)
        return (
            build_workflow_draft_content(
                draft=draft,
                validation=validation_data,
                principal=principal,
                source_revision=source_revision,
            ),
            draft is None,
            not validation_current or not publication_pending,
        )

    @app.callback(
        Output(workflow_result_id(MATCH), 'children', allow_duplicate=True),
        Output(workflow_validation_id(MATCH), 'data'),
        Input(workflow_action_id(MATCH, 'validate'), 'n_clicks'),
        State(workflow_draft_id(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def validate_configuration(
        clicks: int,
        draft_data: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if not isinstance(trigger, dict) or not _click_is_real(clicks):
            return no_update, no_update
        principal = definition.principal_provider()
        try:
            draft = _require_draft(draft_data, principal)
            result = coordinator.validate_draft(
                str(trigger.get('module', '')),
                principal,
                draft.payload,
            )
            if result.draft_revision != draft.revision:
                raise ManagerProjectionError(
                    'Validated draft revision does not match browser draft'
                )
        except ManagerError as error:
            return _error_message(str(error)), no_update
        except Exception:
            return _error_message('Validation could not be completed'), no_update
        validation = {
            'draft_revision': result.draft_revision,
            'valid': result.valid,
            'validated_by': result.audit.actor,
            'validated_at': result.audit.occurred_at.isoformat(),
            'issues': [_issue_document(issue) for issue in result.issues],
        }
        return None, validation

    @app.callback(
        Output(workflow_result_id(MATCH), 'children', allow_duplicate=True),
        Output(workflow_refresh_signal_id(MATCH), 'data', allow_duplicate=True),
        Output(workflow_draft_id(MATCH), 'data', allow_duplicate=True),
        Input(workflow_action_id(MATCH, 'publish'), 'n_clicks'),
        State(workflow_draft_id(MATCH), 'data'),
        State(workflow_validation_id(MATCH), 'data'),
        State(workflow_refresh_signal_id(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def publish_configuration(
        clicks: int,
        draft_data: dict[str, object] | None,
        validation_data: dict[str, object] | None,
        refresh_signal: int | None,
    ):
        trigger = ctx.triggered_id
        if not isinstance(trigger, dict) or not _click_is_real(clicks):
            return no_update, no_update, no_update
        principal = definition.principal_provider()
        try:
            draft = _require_draft(draft_data, principal)
            if not _validation_is_current(draft, validation_data):
                raise ManagerProjectionError('A successful draft validation is required')
            module_key = str(trigger.get('module', ''))
            result = coordinator.publish_draft(
                module_key,
                principal,
                draft.payload,
                draft.base_source_revision,
            )
            updated_draft = draft.with_base_source_revision(result.source_revision)
        except ManagerError as error:
            return _error_message(str(error)), no_update, no_update
        except Exception:
            return _error_message('Configuration could not be published'), no_update, no_update
        return (
            None,
            int(refresh_signal or 0) + 1,
            updated_draft.to_document(),
        )

    @app.callback(
        Output(workflow_result_id(MATCH), 'children', allow_duplicate=True),
        Output(workflow_draft_id(MATCH), 'data', allow_duplicate=True),
        Output(workflow_validation_id(MATCH), 'data', allow_duplicate=True),
        Input(history_load_id(MATCH, ALL, ALL), 'n_clicks'),
        State(history_load_id(MATCH, ALL, ALL), 'id'),
        State(workflow_revision_id(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def load_history_as_draft(
        clicks: list[int],
        load_ids: list[dict[str, object]],
        revision_state: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, clicks, load_ids):
            return no_update, no_update, no_update
        principal = definition.principal_provider()
        try:
            payload = coordinator.load_history_revision(
                str(trigger.get('module', '')),
                principal,
                str(trigger.get('revision', '')),
            )
            base_source_revision = None
            if revision_state:
                raw = revision_state.get('source_revision')
                base_source_revision = str(raw) if raw else None
            draft = ManagerDraft.create(
                owner_subject_id=principal.subject_id,
                payload=payload,
                base_source_revision=base_source_revision,
            )
        except ManagerError as error:
            return _error_message(str(error)), no_update, no_update
        except Exception:
            return _error_message('History revision could not be loaded'), no_update, no_update
        return None, draft.to_document(), None

    @app.callback(
        Output(workflow_result_id(MATCH), 'children', allow_duplicate=True),
        Output(workflow_refresh_signal_id(MATCH), 'data', allow_duplicate=True),
        Output(workflow_projection_signal_id(MATCH), 'data'),
        Input(workflow_action_id(MATCH, 'project'), 'n_clicks'),
        State(workflow_revision_id(MATCH), 'data'),
        State(workflow_refresh_signal_id(MATCH), 'data'),
        prevent_initial_call=True,
    )
    def project_configuration(
        clicks: int,
        revision_state: dict[str, object] | None,
        refresh_signal: int | None,
    ):
        trigger = ctx.triggered_id
        if not isinstance(trigger, dict) or not _click_is_real(clicks):
            return no_update, no_update, no_update
        source_revision = None if not revision_state else revision_state.get('source_revision')
        if not source_revision:
            return _error_message('A published source revision is required'), no_update, no_update
        module_key = str(trigger.get('module', ''))
        try:
            result = coordinator.project(
                module_key,
                definition.principal_provider(),
                str(source_revision),
            )
        except ManagerError as error:
            return _error_message(str(error)), no_update, no_update
        except Exception:
            return _error_message('Projection could not be completed'), no_update, no_update
        signal = {
            'source_revision': result.source_revision,
            'projection_revision': result.projection_revision,
        }
        return None, int(refresh_signal or 0) + 1, signal


def _load_workflow_state(
    coordinator: ManagerProjectionCoordinator,
    module_key: str,
    principal: ManagerPrincipal,
) -> tuple[ProjectionStatus | None, tuple[object, ...], bool, str | None]:
    try:
        status = coordinator.get_status(module_key, principal)
        history = coordinator.list_history(module_key, principal, limit=20)
        can_load_history = coordinator.can_load_history(module_key, principal)
    except ManagerError as error:
        return None, (), False, str(error)
    except Exception:
        return None, (), False, 'Configuration status could not be loaded'
    return status, history, can_load_history, None


def _active_module(
    registry: ManagerModuleRegistry,
    definition: ManagerSurfaceDefinition,
    pathname: str | None,
):
    default_module = registry.require(definition.default_module_key)
    route = pathname or registry.route_for(default_module)
    module = registry.find_by_route(route)
    if module is None and route == registry.root_route:
        module = default_module
    return module


def _safe_draft(
    data: dict[str, object] | None,
    principal: ManagerPrincipal,
) -> ManagerDraft | None:
    try:
        return _require_draft(data, principal)
    except ManagerError:
        return None


def _require_draft(
    data: dict[str, object] | None,
    principal: ManagerPrincipal,
) -> ManagerDraft:
    if not isinstance(data, dict):
        raise ManagerProjectionError('A browser draft is required')
    draft = ManagerDraft.from_document(data)
    if draft.owner_subject_id != principal.subject_id:
        raise ManagerProjectionError('Browser draft belongs to another user')
    return draft


def _validation_is_current(
    draft: ManagerDraft | None,
    validation: dict[str, object] | None,
) -> bool:
    return bool(
        draft is not None
        and validation
        and validation.get('draft_revision') == draft.revision
        and validation.get('valid') is True
    )


def _source_revision(revision_state: dict[str, object] | None) -> str | None:
    if not revision_state:
        return None
    value = revision_state.get('source_revision')
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _issue_document(issue: ProjectionIssue) -> dict[str, object]:
    return {
        'code': issue.code,
        'message': issue.message,
        'level': issue.level,
        'path': issue.path,
    }


def _error_message(message: str):
    from dash import html

    return html.Div(
        message,
        className='atlanticus-manager__message atlanticus-manager__message--error',
    )


def _click_is_real(clicks: int | None) -> bool:
    return isinstance(clicks, int) and not isinstance(clicks, bool) and clicks > 0


def _pattern_click_is_real(
    trigger: object,
    clicks: list[int | None] | None,
    ids: list[dict[str, object]] | None,
) -> bool:
    if not isinstance(trigger, dict):
        return False
    target = dict(trigger)
    for item_id, click_count in zip(ids or [], clicks or [], strict=False):
        if dict(item_id) == target:
            return _click_is_real(click_count)
    return False


def _workflow_revision_state(
    status: ProjectionStatus | None,
) -> dict[str, object] | None:
    if status is None:
        return None
    return {
        'source_revision': status.source_revision,
        'active_source_revision': status.active_source_revision,
    }


def _can_project(status: ProjectionStatus | None) -> bool:
    return bool(
        status
        and status.source_revision
        and status.active_source_revision != status.source_revision
    )


def _safe_state(value: str) -> ProjectionState:
    try:
        return ProjectionState(value)
    except ValueError:
        return ProjectionState.UNAVAILABLE


def _state_label(state: ProjectionState) -> str:
    labels = {
        ProjectionState.NO_SOURCE: 'Sin fuente',
        ProjectionState.SYNCHRONIZED: 'Actualizada',
        ProjectionState.READY: 'Lista',
        ProjectionState.UNAVAILABLE: 'No disponible',
    }
    return labels[state]


def _state_class(state: ProjectionState) -> str:
    return f'atlanticus-manager__state atlanticus-manager__state--{state.value}'


def _panel_class(active: bool) -> str:
    base = 'atlanticus-manager__section-panel'
    return f'{base} {base}--active' if active else base


def _tab_class(active: bool) -> str:
    base = 'atlanticus-manager__tab'
    return f'{base} {base}--active' if active else base
