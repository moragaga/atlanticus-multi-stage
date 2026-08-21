# Los IDs del Manager están namespaced; REFRESH_SIGNAL_ID desacopla la Surface del botón de recarga propio del host standalone.
LOCATION_ID = 'atlanticus-manager-location'
SUMMARY_ID = 'atlanticus-manager-summary'
SIDEBAR_ID = 'atlanticus-manager-sidebar'
SIDEBAR_BACKDROP_ID = 'atlanticus-manager-sidebar-backdrop'
SIDEBAR_TOGGLE_ID = 'atlanticus-manager-sidebar-toggle'
SIDEBAR_CLOSE_ID = 'atlanticus-manager-sidebar-close'
SIDEBAR_MODULES_ID = 'atlanticus-manager-sidebar-modules'
CONTENT_ID = 'atlanticus-manager-content'
REFRESH_BUTTON_ID = 'atlanticus-manager-refresh'
STATUS_STORE_ID = 'atlanticus-manager-status-store'
REFRESH_SIGNAL_ID = 'atlanticus-manager-refresh-signal'


def workflow_action_id(module_key: str, action: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-action',
        'module': module_key,
        'action': action,
    }


def workflow_result_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-result',
        'module': module_key,
    }


def workflow_revision_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-revision',
        'module': module_key,
    }


def workflow_status_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-status',
        'module': module_key,
    }


def workflow_draft_status_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-draft-status',
        'module': module_key,
    }


def workflow_history_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-history',
        'module': module_key,
    }


def module_status_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-module-status',
        'module': module_key,
    }


def workflow_refresh_signal_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-refresh-signal',
        'module': module_key,
    }


def workflow_projection_signal_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-projection-signal',
        'module': module_key,
    }


def workflow_draft_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-draft',
        'module': module_key,
    }


def workflow_validation_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-workflow-validation',
        'module': module_key,
    }


def module_section_store_id(module_key: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-module-section-store',
        'module': module_key,
    }


def module_section_button_id(module_key: str, section: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-module-section-button',
        'module': module_key,
        'section': section,
    }


def module_section_panel_id(module_key: str, section: str) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-module-section-panel',
        'module': module_key,
        'section': section,
    }


def history_load_id(
    module_key: str,
    revision: str,
    occurrence: str,
) -> dict[str, str]:
    return {
        'type': 'atlanticus-manager-history-load',
        'module': module_key,
        'revision': revision,
        'occurrence': occurrence,
    }
