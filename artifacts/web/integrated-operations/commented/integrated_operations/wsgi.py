# Espejo comentado: export WSGI para Gunicorn.
from .application import create_app

runtime = create_app()
server = runtime.server
