# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import sys

from .app import F2Commander
from .config import user_config, ConfigError


def unsafe_main():
    try:
        config = user_config()
    except ConfigError as err:
        print("Application could not start because of malformed configuration:")
        print(err)
        sys.exit(1)
    else:
        app = F2Commander(config)
        app.run()


def main():
    try:
        unsafe_main()
    except Exception as ex:
        print("Fatal error in the appliaction:")
        print(ex)
        sys.exit(2)
