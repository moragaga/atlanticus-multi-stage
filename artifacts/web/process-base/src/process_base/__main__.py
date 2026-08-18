from atlanticus.web.application import run_web_application

from .application import create_app


def main() -> None:
    run_web_application(create_app())


if __name__ == '__main__':
    main()
