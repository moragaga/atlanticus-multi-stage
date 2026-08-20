# Entrada WSGI mínima para el Dockerfile Web transversal.
from integrated_operations.application.wsgi import app

__all__ = ['app']
