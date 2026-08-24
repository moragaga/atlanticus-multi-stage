# Espejo comentado de código productivo.
from atlanticus.web.application import run_web_application
from integrated_operations.application.runtime import create_application_runtime


def main() -> None:
    runtime = create_application_runtime()
    try:
        run_web_application(runtime.web)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
