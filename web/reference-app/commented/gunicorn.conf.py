# Configura Gunicorn desde la capacidad detectada por Atlanticus Web y evita access logs verbosos.
from atlanticus.web import resolve_gunicorn_capacity

bind = '0.0.0.0:8000'
worker_class = 'gthread'
errorlog = '-'
accesslog = None
loglevel = 'info'
timeout = 90
keepalive = 5
capture_output = True

capacity = resolve_gunicorn_capacity()
workers = capacity.workers
threads = capacity.threads


def on_starting(server):
    server.log.info(
        'Atlanticus Gunicorn capacity workers=%s threads=%s cpu=%s '
        'cpu_source=%s memory_gib=%s memory_source=%s',
        capacity.workers,
        capacity.threads,
        capacity.effective_cpu,
        capacity.cpu_source,
        capacity.memory_gib,
        capacity.memory_source,
    )
