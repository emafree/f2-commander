# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

from pathlib import Path

from f2.fs.util import shorten


def test_shorten():
    long_path = "/very/long/path/to/some/directory/and/a/file/in/it/file.txt"

    assert shorten(long_path, width_target=999) == long_path

    assert (
        shorten(long_path, width_target=50, method="truncate")
        == "/very/long/path/to/some/directory/and/a/file/in..."
    )

    with_home = str(Path.home() / long_path[1:])
    assert (
        shorten(with_home, width_target=50, method="truncate", unexpand_home=True)
        == "~/very/long/path/to/some/directory/and/a/file/i..."
    )

    assert (
        shorten(long_path, width_target=50, method="slice")
        == "/very/long/path/to/some/.../a/file/in/it/file.txt"
    )

    unspliceable = "/looong/naaaaaaaaame.txt"
    assert shorten(unspliceable, width_target=10, method="slice") == "/looong..."
