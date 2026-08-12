from atlanticus_web_reference.application import create_app

runtime = create_app()
server = runtime.server
dash_app = runtime.dash
