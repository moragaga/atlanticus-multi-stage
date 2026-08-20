# ADA Integrated Operations

Artifact Web autónomo de Operaciones Integradas. El dashboard principal vive en `/`.

## Responsabilidades

- `application/`: composición Web, runtime y lifecycle WSGI por worker.
- `deployment/`: contrato de environment, identidad y prepare SharePoint → Cosmos.
- `pages/`: rutas Dash de esta aplicación.
- `tool/`: configuración y composición concreta de Operaciones Integradas.
- `runtime/`: repositorios/snapshots temporales usados por el dashboard.
- `resources/`: CSS/JS fuente de la aplicación; `assets/` es publicación generada por Atlanticus.

La aplicación usa `deployment/web/Dockerfile` y dependencias internas desde `wheels/`.
