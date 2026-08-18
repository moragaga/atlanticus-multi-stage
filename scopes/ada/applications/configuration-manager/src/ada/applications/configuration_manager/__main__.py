from pathlib import Path

from ada.applications.configuration_manager.application import (
    create_configuration_manager_application,
)
from ada.applications.configuration_manager.local import build_local_dependencies


def main() -> None:
    runtime = create_configuration_manager_application(
        dependencies=build_local_dependencies(),
        publications_root=Path.cwd() / '.runtime' / 'assets',
    )
    runtime.dash.run(debug=True)


if __name__ == '__main__':
    main()
