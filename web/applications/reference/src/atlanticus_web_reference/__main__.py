from atlanticus.web.application import run_web_application
from atlanticus_web_reference.application import create_app

runtime = create_app()
run_web_application(runtime)
