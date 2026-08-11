from ada_ui_reference.application import create_app
from atlanticus.web.application import run_web_application


def main() -> None:
    run_web_application(create_app())


if __name__ == '__main__':
    main()
