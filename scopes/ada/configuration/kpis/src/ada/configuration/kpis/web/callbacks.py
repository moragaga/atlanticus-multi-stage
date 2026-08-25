from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from dash import ALL, Input, Output, State, ctx, html, no_update

from ada.configuration.kpis.bundle import build_kpi_configuration_digest
from ada.configuration.kpis.models import KpiBinding, KpiConfiguration
from ada.configuration.kpis.web.ids import (
    ADD_BINDING_ID,
    BINDING_CANCEL_ID,
    BINDING_DESTINATIONS_ID,
    BINDING_KEY_ID,
    BINDING_LATEST_ID,
    BINDING_MODAL_ID,
    BINDING_MODAL_TITLE_ID,
    BINDING_RESULT_ID,
    BINDING_SAVE_ID,
    BINDING_SERIES_HOURS_FIELD_ID,
    BINDING_SERIES_HOURS_ID,
    BINDING_SERIES_ID,
    BINDINGS_LIST_ID,
    CONFIGURATION_STORE_ID,
    DESTINATIONS_STORE_ID,
    EDITOR_ID,
    EDITOR_STORE_ID,
    MOUNT_STORE_ID,
    PROTECTED_DETAIL_ID,
    PROTECTED_ID,
    SAVE_BUTTON_ID,
    SAVE_RESULT_ID,
    SOURCE_REVISION_STORE_ID,
    TOOL_PROJECTION_REVISION_ID,
    binding_delete_id,
    binding_edit_id,
)
from ada.configuration.kpis.web.models import KpiAdminWebContext

_MODAL_CLOSED = 'ada-kpis-admin__modal'
_MODAL_OPEN = 'ada-kpis-admin__modal ada-kpis-admin__modal--open'
_EDITOR = 'ada-kpis-admin__editor'
_EDITOR_HIDDEN = 'ada-kpis-admin__editor ada-kpis-admin__editor--hidden'
_PROTECTED = 'ada-kpis-admin__protected'
_PROTECTED_HIDDEN = 'ada-kpis-admin__protected ada-kpis-admin__protected--hidden'
_SERIES_HOURS = 'ada-kpis-admin__series-hours'
_SERIES_HOURS_HIDDEN = 'ada-kpis-admin__series-hours ada-kpis-admin__series-hours--hidden'
_BROWSER_DRAFT_SCHEMA_VERSION = 1


def register_kpi_admin_callbacks(app: object, context: KpiAdminWebContext) -> None:
    @app.callback(
        Output(DESTINATIONS_STORE_ID, 'data'),
        Output(PROTECTED_ID, 'className'),
        Output(EDITOR_ID, 'className'),
        Output(PROTECTED_DETAIL_ID, 'children'),
        Output(TOOL_PROJECTION_REVISION_ID, 'children'),
        Output(ADD_BINDING_ID, 'disabled'),
        Output(SAVE_BUTTON_ID, 'disabled'),
        Output(context.workflow_tab_id, 'style'),
        Output(context.workflow_panel_id, 'style'),
        Output(context.content_panel_id, 'style'),
        Input(MOUNT_STORE_ID, 'data'),
        Input(context.workflow_refresh_signal_id, 'data'),
    )
    def load_destination_catalog(_mounted: object, _refresh_signal: object):
        try:
            catalog = context.services.destinations.load()
        except Exception:
            catalog = None
        if catalog is None:
            return (
                None,
                _PROTECTED,
                _EDITOR_HIDDEN,
                (
                    'No hay una Tool Projection administrativa disponible. Configura, publica '
                    'y proyecta una herramienta ADA antes de configurar KPIs.'
                ),
                'No disponible',
                True,
                True,
                {'display': 'none'},
                {'display': 'none'},
                {'display': 'block'},
            )
        document = {
            'tool_projection_revision': catalog.tool_projection_revision,
            'destinations': [
                {'key': destination.key, 'display_name': destination.display_name}
                for destination in catalog.destinations
            ],
        }
        return (
            document,
            _PROTECTED_HIDDEN,
            _EDITOR,
            '',
            catalog.tool_projection_revision[:12],
            not bool(catalog.destinations),
            False,
            {},
            {},
            {},
        )

    @app.callback(
        Output(CONFIGURATION_STORE_ID, 'data', allow_duplicate=True),
        Output(SOURCE_REVISION_STORE_ID, 'data', allow_duplicate=True),
        Input(context.draft_store_id, 'data'),
        prevent_initial_call='initial_duplicate',
    )
    def load_browser_draft(draft_data: dict[str, object] | None):
        if draft_data is None:
            return no_update, no_update
        try:
            configuration = _configuration_from_browser_draft(
                draft_data,
                context.draft_owner_provider(),
            )
        except Exception:
            return KpiConfiguration().to_document(), None
        return (
            configuration.to_document(),
            _draft_base_source_revision(
                draft_data,
                owner_subject_id=context.draft_owner_provider(),
                fallback=None,
            ),
        )

    @app.callback(
        Output(context.editor_revision_store_id, 'data'),
        Input(CONFIGURATION_STORE_ID, 'data'),
    )
    def track_editor_revision(configuration_data: dict[str, object] | None):
        try:
            return build_kpi_configuration_digest(_configuration(configuration_data))
        except Exception:
            return _raw_editor_revision(configuration_data)

    @app.callback(
        Output(BINDINGS_LIST_ID, 'children'),
        Input(CONFIGURATION_STORE_ID, 'data'),
        Input(DESTINATIONS_STORE_ID, 'data'),
    )
    def render_bindings(
        configuration_data: dict[str, object] | None,
        destinations_data: dict[str, object] | None,
    ):
        configuration = _configuration(configuration_data)
        if not configuration.bindings:
            if _destination_document(destinations_data) is None:
                return _empty('La Tool Projection debe estar disponible para configurar KPIs.')
            if not _destination_options(destinations_data):
                return _empty('La Tool Projection no expone componentes que acepten KPI.')
            return _empty('No hay KPIs configurados. Agrega el primer KPI para comenzar.')
        names = _destination_names(destinations_data)
        return [
            _binding_card(binding, destination_names=names) for binding in configuration.bindings
        ]

    @app.callback(
        Output(BINDING_MODAL_ID, 'className'),
        Output(EDITOR_STORE_ID, 'data'),
        Output(BINDING_MODAL_TITLE_ID, 'children'),
        Output(BINDING_KEY_ID, 'value'),
        Output(BINDING_KEY_ID, 'disabled'),
        Output(BINDING_DESTINATIONS_ID, 'value'),
        Output(BINDING_LATEST_ID, 'value'),
        Output(BINDING_SERIES_ID, 'value'),
        Output(BINDING_SERIES_HOURS_ID, 'value'),
        Output(BINDING_RESULT_ID, 'children'),
        Output(CONFIGURATION_STORE_ID, 'data', allow_duplicate=True),
        Input(ADD_BINDING_ID, 'n_clicks'),
        Input(binding_edit_id(ALL), 'n_clicks'),
        Input(BINDING_CANCEL_ID, 'n_clicks'),
        Input(BINDING_CANCEL_ID + '-header', 'n_clicks'),
        Input(BINDING_CANCEL_ID + '-footer', 'n_clicks'),
        Input(BINDING_SAVE_ID, 'n_clicks'),
        State(binding_edit_id(ALL), 'id'),
        State(EDITOR_STORE_ID, 'data'),
        State(BINDING_KEY_ID, 'value'),
        State(BINDING_DESTINATIONS_ID, 'value'),
        State(BINDING_LATEST_ID, 'value'),
        State(BINDING_SERIES_ID, 'value'),
        State(BINDING_SERIES_HOURS_ID, 'value'),
        State(CONFIGURATION_STORE_ID, 'data'),
        State(DESTINATIONS_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def edit_binding(
        add_clicks: int | None,
        edit_clicks: list[int | None] | None,
        cancel_clicks: int | None,
        header_cancel_clicks: int | None,
        footer_cancel_clicks: int | None,
        save_clicks: int | None,
        edit_ids: list[dict[str, object]] | None,
        editor_data: dict[str, object] | None,
        key_value: str | None,
        destination_values: list[str] | None,
        latest_values: list[str] | None,
        series_values: list[str] | None,
        series_hours: int | float | None,
        configuration_data: dict[str, object] | None,
        destinations_data: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if _matches_trigger(
            trigger,
            BINDING_CANCEL_ID,
            BINDING_CANCEL_ID + '-header',
            BINDING_CANCEL_ID + '-footer',
        ):
            return _modal_closed_response()
        if trigger == ADD_BINDING_ID:
            if not _click_is_real(add_clicks):
                return _modal_no_update_response()
            if _destination_document(destinations_data) is None:
                return _modal_closed_response()
            return (
                _MODAL_OPEN,
                {'mode': 'create'},
                'Agregar KPI',
                '',
                False,
                [],
                ['enabled'],
                [],
                24,
                '',
                no_update,
            )
        if _pattern_click_is_real(trigger, edit_clicks, edit_ids):
            configuration = _configuration(configuration_data)
            binding = configuration.binding(str(trigger.get('key', '')))
            if binding is None:
                return _modal_closed_response()
            return (
                _MODAL_OPEN,
                {'mode': 'edit', 'key': binding.key},
                'Editar KPI',
                binding.key,
                True,
                list(binding.destination_keys),
                ['enabled'] if binding.latest_enabled else [],
                ['enabled'] if binding.series_enabled else [],
                binding.series_hours if binding.series_hours is not None else 24,
                '',
                no_update,
            )
        if trigger != BINDING_SAVE_ID or not _click_is_real(save_clicks):
            return _modal_no_update_response()
        if not context.can_manage():
            return _modal_error_response(
                editor_data,
                key_value,
                destination_values,
                latest_values,
                series_values,
                series_hours,
                'Management access is denied',
            )
        if _destination_document(destinations_data) is None:
            return _modal_error_response(
                editor_data,
                key_value,
                destination_values,
                latest_values,
                series_values,
                series_hours,
                'Tool projection is not available',
            )
        try:
            configuration = _configuration(configuration_data)
            mode = str((editor_data or {}).get('mode', 'create'))
            existing_key = str((editor_data or {}).get('key', '')).strip()
            key = existing_key if mode == 'edit' else str(key_value or '').strip()
            series_enabled = 'enabled' in (series_values or [])
            binding = KpiBinding(
                key=key,
                destination_keys=tuple(str(value) for value in (destination_values or [])),
                latest_enabled='enabled' in (latest_values or []),
                series_enabled=series_enabled,
                series_hours=_series_hours(series_hours) if series_enabled else None,
            )
            updated = (
                configuration.replace_binding(binding)
                if mode == 'edit'
                else configuration.add_binding(binding)
            )
        except Exception as error:
            return _modal_error_response(
                editor_data,
                key_value,
                destination_values,
                latest_values,
                series_values,
                series_hours,
                str(error),
            )
        return (
            _MODAL_CLOSED,
            None,
            'Agregar KPI',
            '',
            False,
            [],
            ['enabled'],
            [],
            24,
            '',
            updated.to_document(),
        )

    @app.callback(
        Output(BINDING_DESTINATIONS_ID, 'options'),
        Input(DESTINATIONS_STORE_ID, 'data'),
        Input(EDITOR_STORE_ID, 'data'),
        State(CONFIGURATION_STORE_ID, 'data'),
    )
    def render_destination_options(
        destinations_data: dict[str, object] | None,
        editor_data: dict[str, object] | None,
        configuration_data: dict[str, object] | None,
    ):
        options = _destination_options(destinations_data)
        known = {str(option['value']) for option in options}
        if str((editor_data or {}).get('mode', '')) != 'edit':
            return options
        binding = _configuration(configuration_data).binding(
            str((editor_data or {}).get('key', ''))
        )
        if binding is None:
            return options
        for key in binding.destination_keys:
            if key in known:
                continue
            options.append(
                {
                    'label': f'{key} · no disponible en Tool Projection',
                    'value': key,
                    'disabled': True,
                }
            )
        return options

    @app.callback(
        Output(BINDING_SERIES_HOURS_FIELD_ID, 'className'),
        Input(BINDING_SERIES_ID, 'value'),
    )
    def toggle_series_hours(series_values: list[str] | None) -> str:
        return _SERIES_HOURS if 'enabled' in (series_values or []) else _SERIES_HOURS_HIDDEN

    @app.callback(
        Output(CONFIGURATION_STORE_ID, 'data', allow_duplicate=True),
        Input(binding_delete_id(ALL), 'n_clicks'),
        State(binding_delete_id(ALL), 'id'),
        State(CONFIGURATION_STORE_ID, 'data'),
        prevent_initial_call=True,
    )
    def delete_binding(
        clicks: list[int | None] | None,
        ids: list[dict[str, object]] | None,
        configuration_data: dict[str, object] | None,
    ):
        trigger = ctx.triggered_id
        if not _pattern_click_is_real(trigger, clicks, ids):
            return no_update
        if not context.can_manage():
            return no_update
        try:
            updated = _configuration(configuration_data).remove_binding(str(trigger.get('key', '')))
        except Exception:
            return no_update
        return updated.to_document()

    @app.callback(
        Output(CONFIGURATION_STORE_ID, 'data', allow_duplicate=True),
        Output(SAVE_RESULT_ID, 'children'),
        Output(context.draft_store_id, 'data', allow_duplicate=True),
        Input(SAVE_BUTTON_ID, 'n_clicks'),
        Input(context.draft_save_action_id, 'n_clicks'),
        State(CONFIGURATION_STORE_ID, 'data'),
        State(SOURCE_REVISION_STORE_ID, 'data'),
        State(context.draft_store_id, 'data'),
        prevent_initial_call=True,
    )
    def save_kpi_draft(
        content_clicks: int | None,
        workflow_clicks: int | None,
        configuration_data: dict[str, object] | None,
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
            return no_update, no_update, no_update
        if not context.can_manage():
            return no_update, _error('Management access is denied'), no_update
        try:
            if context.services.destinations.load() is None:
                raise ValueError('Tool projection is not available')
            configuration = _configuration(configuration_data)
            base_revision = _draft_base_source_revision(
                current_draft,
                owner_subject_id=context.draft_owner_provider(),
                fallback=source_revision,
            )
            draft = _browser_draft_document(
                configuration=configuration,
                owner_subject_id=context.draft_owner_provider(),
                base_source_revision=base_revision,
            )
        except Exception as error:
            return no_update, _error(str(error)), no_update
        return configuration.to_document(), None, draft


def _configuration(data: dict[str, object] | None) -> KpiConfiguration:
    if not isinstance(data, dict):
        return KpiConfiguration()
    return KpiConfiguration.from_document(data)


def _configuration_from_browser_draft(
    data: dict[str, object] | None,
    owner_subject_id: str,
) -> KpiConfiguration:
    if not isinstance(data, dict) or data.get('schema_version') != _BROWSER_DRAFT_SCHEMA_VERSION:
        raise ValueError('Browser draft does not exist')
    if str(data.get('owner_subject_id', '')).strip() != owner_subject_id.strip():
        raise ValueError('Browser draft belongs to another user')
    payload = data.get('payload')
    if not isinstance(payload, dict):
        raise ValueError('Browser draft payload is invalid')
    configuration = KpiConfiguration.from_document(dict(payload))
    revision = build_kpi_configuration_digest(configuration)
    if str(data.get('revision', '')).strip() != revision:
        raise ValueError('Browser draft revision does not match content')
    return configuration


def _browser_draft_document(
    *,
    configuration: KpiConfiguration,
    owner_subject_id: str,
    base_source_revision: str | None,
) -> dict[str, object]:
    owner = owner_subject_id.strip()
    if not owner:
        raise ValueError('Browser draft owner is required')
    return {
        'schema_version': _BROWSER_DRAFT_SCHEMA_VERSION,
        'owner_subject_id': owner,
        'revision': build_kpi_configuration_digest(configuration),
        'saved_at': datetime.now(UTC).isoformat(),
        'base_source_revision': base_source_revision,
        'payload': configuration.to_document(),
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


def _destination_document(data: dict[str, object] | None) -> dict[str, object] | None:
    if not isinstance(data, dict):
        return None
    revision = str(data.get('tool_projection_revision', '')).strip()
    destinations = data.get('destinations')
    if not revision or not isinstance(destinations, list):
        return None
    return data


def _destination_options(data: dict[str, object] | None) -> list[dict[str, object]]:
    document = _destination_document(data)
    if document is None:
        return []
    options = []
    for item in document['destinations']:
        if not isinstance(item, dict):
            continue
        key = str(item.get('key', '')).strip()
        display_name = str(item.get('display_name', '')).strip()
        if key and display_name:
            options.append({'label': display_name, 'value': key})
    return options


def _destination_names(data: dict[str, object] | None) -> dict[str, str]:
    return {str(option['value']): str(option['label']) for option in _destination_options(data)}


def _binding_card(binding: KpiBinding, *, destination_names: dict[str, str]) -> object:
    channels = []
    if binding.latest_enabled:
        channels.append(html.Span('Latest', className='ada-kpis-admin__badge'))
    if binding.series_enabled:
        channels.append(
            html.Span(
                f'Series · {binding.series_hours} h',
                className='ada-kpis-admin__badge',
            )
        )
    if not binding.enabled:
        channels.append(
            html.Span('Desactivado', className='ada-kpis-admin__badge ada-kpis-admin__badge--muted')
        )
    destinations = [
        html.Span(
            destination_names.get(key, f'{key} · no disponible'),
            className=(
                'ada-kpis-admin__destination'
                if key in destination_names
                else 'ada-kpis-admin__destination ada-kpis-admin__destination--missing'
            ),
        )
        for key in binding.destination_keys
    ]
    return html.Article(
        [
            html.Div(
                [
                    html.Div(
                        [html.Strong(binding.key), html.Div(channels)],
                        className='ada-kpis-admin__binding-copy',
                    ),
                    html.Div(destinations, className='ada-kpis-admin__destinations'),
                ],
                className='ada-kpis-admin__binding-main',
            ),
            html.Div(
                [
                    html.Button(
                        'Editar',
                        id=binding_edit_id(binding.key),
                        n_clicks=0,
                        className='ada-kpis-admin__binding-action',
                    ),
                    html.Button(
                        'Eliminar',
                        id=binding_delete_id(binding.key),
                        n_clicks=0,
                        className='ada-kpis-admin__binding-action ada-kpis-admin__binding-action--danger',
                    ),
                ],
                className='ada-kpis-admin__binding-actions',
            ),
        ],
        className='ada-kpis-admin__binding-card',
    )


def _empty(message: str) -> object:
    return html.Div(message, className='ada-kpis-admin__empty')


def _series_hours(value: int | float | None) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError('KPI series hours must be a positive integer when series is enabled')
    numeric = float(value)
    if not numeric.is_integer() or numeric <= 0:
        raise ValueError('KPI series hours must be a positive integer when series is enabled')
    return int(numeric)


def _matches_trigger(trigger: object, *ids: str) -> bool:
    return isinstance(trigger, str) and trigger in ids


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
        if dict(item_id) == target and _click_is_real(click_count):
            return True
    return False


def _save_draft_click_is_real(
    trigger: object,
    *,
    content_clicks: int | None,
    workflow_clicks: int | None,
    workflow_id: object,
) -> bool:
    if trigger == SAVE_BUTTON_ID:
        return _click_is_real(content_clicks)
    if trigger == workflow_id:
        return _click_is_real(workflow_clicks)
    return False


def _raw_editor_revision(configuration_data: dict[str, object] | None) -> str:
    encoded = json.dumps(
        configuration_data,
        sort_keys=True,
        separators=(',', ':'),
        default=str,
    ).encode('utf-8')
    return f'editor:{hashlib.sha256(encoded).hexdigest()}'


def _modal_closed_response():
    return (
        _MODAL_CLOSED,
        None,
        'Agregar KPI',
        '',
        False,
        [],
        ['enabled'],
        [],
        24,
        '',
        no_update,
    )


def _modal_no_update_response():
    return (no_update,) * 11


def _modal_error_response(
    editor_data: dict[str, object] | None,
    key_value: str | None,
    destination_values: list[str] | None,
    latest_values: list[str] | None,
    series_values: list[str] | None,
    series_hours: int | float | None,
    message: str,
):
    return (
        _MODAL_OPEN,
        editor_data,
        'Editar KPI' if str((editor_data or {}).get('mode', '')) == 'edit' else 'Agregar KPI',
        key_value,
        str((editor_data or {}).get('mode', '')) == 'edit',
        destination_values,
        latest_values,
        series_values,
        series_hours,
        _error(message),
        no_update,
    )


def _error(message: str) -> object:
    return html.Div(
        message,
        className='ada-kpis-admin__message ada-kpis-admin__message--error',
    )
