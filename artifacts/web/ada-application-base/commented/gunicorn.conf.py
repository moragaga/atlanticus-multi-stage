from atlanticus.web.hosting import resolve_gunicorn_capacity

bind = '0.0.0.0:8000'
worker_class = 'gthread'
errorlog = '-'
accesslog = None
loglevel = 'info'
timeout = 90
keepalive = 5
capture_output = True

# La capacidad transversal sigue definiendo workers e hilos según los recursos del contenedor.
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


# Gunicorn ejecuta este hook dentro del worker una vez inicializada la aplicación WSGI.
def post_worker_init(worker):
    warmup = getattr(worker.wsgi, 'warmup', None)
    if not callable(warmup):
        raise RuntimeError('Gunicorn WSGI application does not support worker warmup')
    # La composición Dash y la infraestructura se crean antes del primer request y después del fork.
    warmup()


# El runtime se cierra explícitamente en el mismo proceso worker que lo abrió.
def worker_exit(_server, worker):
    close = getattr(worker.wsgi, 'close', None)
    if callable(close):
        close()
