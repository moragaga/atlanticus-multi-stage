from ada_application_base.application import create_application_runtime
from atlanticus.web.application import run_web_application


def main() -> None:
    runtime = create_application_runtime()
    try:
        run_web_application(runtime.web)
    finally:
        runtime.close()


if __name__ == '__main__':
    main()
