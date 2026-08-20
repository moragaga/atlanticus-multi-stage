from __future__ import annotations

import argparse
from collections.abc import Sequence

from ada.compositions.web_deployment import prepare_ada_web_deployment

from ada_application_base.definition import build_deployment_definition


def main(argv: Sequence[str] | None = None) -> None:
    arguments = _parser().parse_args(argv)
    # Prepare permanece separado del runtime y sólo crea DB si el comando lo pide explícitamente.
    prepare_ada_web_deployment(
        definition=build_deployment_definition(),
        create_databases_if_missing=arguments.create_database_if_missing,
        actor=arguments.actor,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ada-application-base-prepare')
    parser.add_argument('--create-database-if-missing', action='store_true')
    parser.add_argument('--actor', default='ada-bootstrap')
    return parser


if __name__ == '__main__':
    main()
