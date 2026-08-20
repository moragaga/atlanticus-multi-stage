from atlanticus.web.hosting import resolve_gunicorn_capacity

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


def post_worker_init(worker):
    warmup = getattr(worker.wsgi, 'warmup', None)
    if not callable(warmup):
        raise RuntimeError('Gunicorn WSGI application does not support worker warmup')
    warmup()


def worker_exit(_server, worker):
    close = getattr(worker.wsgi, 'close', None)
    if callable(close):
        close()
