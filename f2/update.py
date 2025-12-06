# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import json
import urllib.request
from importlib.metadata import version
from typing import Tuple


def current_version() -> str:
    return version("f2-commander")


def check_for_updates() -> Tuple[str, str]:
    """Check if a newer version is available on PyPI."""
    with urllib.request.urlopen("https://pypi.org/pypi/f2-commander/json") as response:
        data = json.load(response)
        latest_version = data["info"]["version"]

    return current_version(), latest_version
