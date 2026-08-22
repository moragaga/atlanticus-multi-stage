from dash import Dash

from ada.configuration.tools.web.callbacks import register_tool_admin_callbacks
from ada.configuration.tools.web.models import ToolAdminWebContext


def test_tool_admin_callbacks_register_with_real_dash_application() -> None:
    app = Dash(__name__)
    context = ToolAdminWebContext(
        services=object(),
        draft_store_id='test-tool-draft-store',
        draft_save_action_id='test-tool-draft-save',
        workflow_refresh_signal_id='test-tool-workflow-refresh',
        editor_revision_store_id='test-tool-editor-revision',
        draft_owner_provider=lambda: 'test-user',
    )

    register_tool_admin_callbacks(app, context)

    assert app.callback_map
