# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

from .app import F2Commander
from .config import init_default_config


def main():
    init_default_config()
    app = F2Commander()
    app.run()
