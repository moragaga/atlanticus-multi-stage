# Espejo comentado de wsgi.py.
from ada.applications.reference.application import create_app

runtime = create_app()
server = runtime.server
