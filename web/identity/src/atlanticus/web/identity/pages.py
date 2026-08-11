from __future__ import annotations

from html import escape

from flask import Response


def invalid_identity_response() -> Response:
    return _page(
        status_code=401,
        title='Credenciales no válidas',
        message='No fue posible validar las credenciales de acceso.',
    )


def user_disabled_response() -> Response:
    return _page(
        status_code=403,
        title='Usuario deshabilitado',
        message='Su usuario no se encuentra habilitado para acceder a esta aplicación.',
    )


def identity_unavailable_response() -> Response:
    return _page(
        status_code=503,
        title='Servicio no disponible',
        message='No fue posible validar el acceso en este momento.',
    )


def _page(*, status_code: int, title: str, message: str) -> Response:
    body = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Atlanticus</title>
<style>
html,body{{height:100%;margin:0;font-family:Arial,sans-serif;background:#f5f5f5;color:#222}}
main{{height:100%;display:grid;place-items:center;padding:24px;box-sizing:border-box}}
section{{max-width:560px;text-align:center}}
h1{{font-size:28px;margin:0 0 12px}}p{{font-size:16px;line-height:1.5;margin:0;color:#555}}
</style>
</head>
<body><main><section><h1>{escape(title)}</h1><p>{escape(message)}</p></section></main></body>
</html>'''
    response = Response(body, status=status_code, content_type='text/html; charset=utf-8')
    response.headers['Cache-Control'] = 'no-store'
    return response
