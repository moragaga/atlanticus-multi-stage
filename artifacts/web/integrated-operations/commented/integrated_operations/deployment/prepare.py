# Deployment: traduce environment resuelto y ejecuta prepare de infraestructura/configuración.
from __future__ import annotations

import argparse
from collections.abc import Sequence

from ada.compositions.web_deployment import prepare_ada_web_deployment
from integrated_operations.deployment.definition import build_deployment_definition


def main(argv: Sequence[str] | None = None) -> None:
    arguments = _parser().parse_args(argv)
    prepare_ada_web_deployment(
        definition=build_deployment_definition(),
        create_databases_if_missing=arguments.create_database_if_missing,
        actor=arguments.actor,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ada-integrated-operations-prepare')
    parser.add_argument('--create-database-if-missing', action='store_true')
    parser.add_argument('--actor', default='ada-bootstrap')
    return parser


if __name__ == '__main__':
    main()
