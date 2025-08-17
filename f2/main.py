# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import sys
from pathlib import Path

import click

from .app import F2Commander
from .config import ConfigError, migrate_legacy_config, user_config, user_config_path
from .errors import log_dir, log_uncaught_error


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=Path),
    default=user_config_path(),
    show_default=True,
    help="Configuraiton file path, will be created if does not exist",
)
@click.option(
    "--debug",
    is_flag=True,
    help=f"Enable local file logging [logs directory: {log_dir()}]",
)
def main(config_path, debug):
    try:
        migrate_legacy_config()
        config = user_config(config_path)
        app = F2Commander(config=config, debug=debug)
        app.run()
    except ConfigError as err:
        click.echo("Application could not start because of malformed configuration:")
        click.echo(err)
        log_uncaught_error(debug_enabled=debug)
        sys.exit(1)
    except Exception as ex:
        click.echo("Fatal error in the appliaction:")
        click.echo(ex)
        log_uncaught_error(debug_enabled=debug)
        sys.exit(2)
