# Aplicación de referencia: demuestra el contrato web sin introducir lógica de negocio real.
from atlanticus.web import run_web_application
from atlanticus_web_reference.application import create_app

# Este entrypoint usa Flask.run y permite debug/reloader cuando ATLANTICUS_ENVIRONMENT es local.
runtime = create_app()
run_web_application(runtime)
