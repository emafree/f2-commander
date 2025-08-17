# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import json
import urllib.request
from importlib.metadata import version
from typing import Tuple

from packaging.version import Version


def check_for_updates() -> Tuple[Version, Version]:
    """Check if a newer version is available on PyPI."""
    current_version = version("f2-commander")

    with urllib.request.urlopen("https://pypi.org/pypi/f2-commander/json") as response:
        data = json.load(response)
        latest_version = data["info"]["version"]

    return Version(current_version), Version(latest_version)
