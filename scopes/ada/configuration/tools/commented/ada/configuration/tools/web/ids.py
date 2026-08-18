# Espejo pedagógico: conserva la misma lógica del archivo productivo.
# Los comentarios documentan la responsabilidad sin cambiar el comportamiento.
# Agrupa IDs propios del editor estructural de Tools.
CATALOG_STORE_ID = 'ada-tools-catalog-store'
SOURCE_REVISION_STORE_ID = 'ada-tools-source-revision-store'
STRUCTURE_STORE_ID = 'ada-tools-structure-store'
DRAFT_LOAD_SIGNAL_ID = 'ada-tools-draft-load-signal'
COMPONENT_EDITOR_STORE_ID = 'ada-tools-component-editor-store'
SUBCOMPONENT_EDITOR_STORE_ID = 'ada-tools-subcomponent-editor-store'
SELECTED_TOOL_ID = 'ada-tools-selected-tool'
CREATE_OPEN_ID = 'ada-tools-create-open'
CREATE_MODAL_ID = 'ada-tools-create-modal'
CREATE_CANCEL_ID = 'ada-tools-create-cancel'
CREATE_NAME_ID = 'ada-tools-create-name'
CREATE_KIND_ID = 'ada-tools-create-kind'
CREATE_BUTTON_ID = 'ada-tools-create-button'
CREATE_RESULT_ID = 'ada-tools-create-result'
TOOL_NAME_ID = 'ada-tools-tool-name'
TOOL_KEY_ID = 'ada-tools-tool-key'
APPLICATION_KEY_ID = 'ada-tools-application-key'
TOOL_KIND_ID = 'ada-tools-tool-kind'
TOOL_SCOPE_ID = 'ada-tools-tool-scope'
SOURCES_ID = 'ada-tools-sources'
PI_FRESHNESS_ID = 'ada-tools-pi-freshness'
DISPATCH_FRESHNESS_ID = 'ada-tools-dispatch-freshness'
PI_FRESHNESS_FIELD_ID = 'ada-tools-pi-freshness-field'
DISPATCH_FRESHNESS_FIELD_ID = 'ada-tools-dispatch-freshness-field'
COMPONENTS_LIST_ID = 'ada-tools-components-list'
SUBCOMPONENTS_LIST_ID = 'ada-tools-subcomponents-list'
STRUCTURE_RESULT_ID = 'ada-tools-structure-result'
ADD_COMPONENT_ID = 'ada-tools-add-component'
ADD_SUBCOMPONENT_ID = 'ada-tools-add-subcomponent'
COMPONENT_MODAL_ID = 'ada-tools-component-modal'
COMPONENT_MODAL_TITLE_ID = 'ada-tools-component-modal-title'
COMPONENT_NAME_ID = 'ada-tools-component-name'
COMPONENT_SCOPE_ID = 'ada-tools-component-scope'
COMPONENT_SCOPE_FIELD_ID = 'ada-tools-component-scope-field'
COMPONENT_PLACEMENT_ID = 'ada-tools-component-placement'
COMPONENT_PLACEMENT_FIELD_ID = 'ada-tools-component-placement-field'
COMPONENT_SAVE_ID = 'ada-tools-component-save'
COMPONENT_CANCEL_ID = 'ada-tools-component-cancel'
COMPONENT_MODAL_RESULT_ID = 'ada-tools-component-modal-result'
SUBCOMPONENT_MODAL_ID = 'ada-tools-subcomponent-modal'
SUBCOMPONENT_MODAL_TITLE_ID = 'ada-tools-subcomponent-modal-title'
SUBCOMPONENT_PARENT_ID = 'ada-tools-subcomponent-parent'
SUBCOMPONENT_NAME_ID = 'ada-tools-subcomponent-name'
SUBCOMPONENT_LINKED_ID = 'ada-tools-subcomponent-linked'
SUBCOMPONENT_LINKED_FIELD_ID = 'ada-tools-subcomponent-linked-field'
SUBCOMPONENT_SAVE_ID = 'ada-tools-subcomponent-save'
SUBCOMPONENT_CANCEL_ID = 'ada-tools-subcomponent-cancel'
SUBCOMPONENT_MODAL_RESULT_ID = 'ada-tools-subcomponent-modal-result'
SAVE_BUTTON_ID = 'ada-tools-save'
SAVE_RESULT_ID = 'ada-tools-save-result'
REFERENCE_ID = 'ada-tools-reference'
IMPORT_UPLOAD_ID = 'ada-tools-import-upload'
IMPORT_RESULT_ID = 'ada-tools-import-result'
SOURCE_NAME_ID = 'ada-tools-source-name'
PROJECTION_NAME_ID = 'ada-tools-projection-name'


def component_edit_id(key: str | object) -> dict[str, object]:
    return {'type': 'ada-tools-component-edit', 'key': key}


def component_delete_id(key: str | object) -> dict[str, object]:
    return {'type': 'ada-tools-component-delete', 'key': key}


def component_move_id(key: str | object, direction: str | object) -> dict[str, object]:
    return {'type': 'ada-tools-component-move', 'key': key, 'direction': direction}


def subcomponent_edit_id(component: str | object, key: str | object) -> dict[str, object]:
    return {'type': 'ada-tools-subcomponent-edit', 'component': component, 'key': key}


def subcomponent_delete_id(component: str | object, key: str | object) -> dict[str, object]:
    return {'type': 'ada-tools-subcomponent-delete', 'component': component, 'key': key}


def subcomponent_move_id(
    component: str | object,
    key: str | object,
    direction: str | object,
) -> dict[str, object]:
    return {
        'type': 'ada-tools-subcomponent-move',
        'component': component,
        'key': key,
        'direction': direction,
    }
