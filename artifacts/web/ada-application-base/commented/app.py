# Expone el WSGI lazy del artifact con el nombre esperado por el Dockerfile Web transversal.
from ada_application_base.wsgi import app

__all__ = ['app']
