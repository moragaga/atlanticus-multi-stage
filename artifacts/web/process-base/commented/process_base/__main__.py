# Espejo comentado: ejecutable local de certificación.
from atlanticus.web.application import run_web_application

from .application import create_app


# Entry point local; delega el arranque al runtime web de Atlanticus.
def main() -> None:
    run_web_application(create_app())


if __name__ == '__main__':
    main()
