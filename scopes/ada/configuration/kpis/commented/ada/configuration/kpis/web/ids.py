# Centraliza IDs Dash estables y pattern IDs de bindings KPI.
# El código bajo estos comentarios conserva paridad ejecutable con producción.
CONFIGURATION_STORE_ID = 'ada-kpis-configuration-store'
SOURCE_REVISION_STORE_ID = 'ada-kpis-source-revision-store'
DESTINATIONS_STORE_ID = 'ada-kpis-destinations-store'
MOUNT_STORE_ID = 'ada-kpis-mount-store'
EDITOR_STORE_ID = 'ada-kpis-binding-editor-store'
PROTECTED_ID = 'ada-kpis-protected'
PROTECTED_DETAIL_ID = 'ada-kpis-protected-detail'
EDITOR_ID = 'ada-kpis-editor'
TOOL_PROJECTION_REVISION_ID = 'ada-kpis-tool-projection-revision'
BINDINGS_LIST_ID = 'ada-kpis-bindings-list'
ADD_BINDING_ID = 'ada-kpis-add-binding'
BINDING_MODAL_ID = 'ada-kpis-binding-modal'
BINDING_MODAL_TITLE_ID = 'ada-kpis-binding-modal-title'
BINDING_KEY_ID = 'ada-kpis-binding-key'
BINDING_DESTINATIONS_ID = 'ada-kpis-binding-destinations'
BINDING_LATEST_ID = 'ada-kpis-binding-latest'
BINDING_SERIES_ID = 'ada-kpis-binding-series'
BINDING_SERIES_HOURS_FIELD_ID = 'ada-kpis-binding-series-hours-field'
BINDING_SERIES_HOURS_ID = 'ada-kpis-binding-series-hours'
BINDING_SAVE_ID = 'ada-kpis-binding-save'
BINDING_CANCEL_ID = 'ada-kpis-binding-cancel'
BINDING_RESULT_ID = 'ada-kpis-binding-result'
SAVE_BUTTON_ID = 'ada-kpis-save'
SAVE_RESULT_ID = 'ada-kpis-save-result'


def binding_edit_id(key: str | object) -> dict[str, object]:
    return {'type': 'ada-kpis-binding-edit', 'key': key}


def binding_delete_id(key: str | object) -> dict[str, object]:
    return {'type': 'ada-kpis-binding-delete', 'key': key}
