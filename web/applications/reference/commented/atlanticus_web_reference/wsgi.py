# Aplicación de referencia: demuestra el contrato web sin introducir lógica de negocio real.
from atlanticus_web_reference.application import create_app

# WSGI solo expone la misma factory; Gunicorn decide cómo hospedar el proceso.
runtime = create_app()
server = runtime.server
dash_app = runtime.dash
