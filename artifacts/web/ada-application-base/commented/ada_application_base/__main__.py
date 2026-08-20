# Entry point local/directo. Gunicorn usa app.py y el WSGI lazy.
from atlanticus.web.application import run_web_application

from ada_application_base.application import create_application_runtime


def main() -> None:
    runtime = create_application_runtime()
    try:
        run_web_application(runtime.web)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
