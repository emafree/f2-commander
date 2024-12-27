# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import ast
from pathlib import Path

import dotenv
import platformdirs

DEFAULT_CONFIG = f"""
dirs_first=True
order_case_sensitive=True
show_hidden=False

theme="'textual-dark'"

bookmarks = "[
  '~',
  '{Path("~") / Path(platformdirs.user_documents_dir()).relative_to(Path.home())}',
  '{Path("~") / Path(platformdirs.user_downloads_dir()).relative_to(Path.home())}',
  '{Path("~") / Path(platformdirs.user_pictures_dir()).relative_to(Path.home())}',
  '{Path("~") / Path(platformdirs.user_videos_dir()).relative_to(Path.home())}',
  '{Path("~") / Path(platformdirs.user_music_dir()).relative_to(Path.home())}',
]"

file_systems = "[
  {{'display_name': 'Rebex.net Demo FTP server', 'protocol': 'ftp', 'host': 'test.rebex.net', 'username': 'demo', 'password': 'password'}},
]"
""".strip()  # noqa: E501


def config_root() -> Path:
    """Path to the directory that hosts all configuration files"""

    root_dir = platformdirs.user_config_path("f2commander")
    if not root_dir.exists():
        root_dir.mkdir()
    return root_dir


def user_config_path() -> Path:
    """Path to the file with user's application config"""

    config_path = config_root() / "user.env"
    if not config_path.exists():
        config_path.touch()
    return config_path


def init_default_config():
    if user_config_path().stat().st_size == 0:
        user_config_path().write_text(DEFAULT_CONFIG)


# FIXME: current Config + InstantConfigAttr implementation is straightforward, but
#        obviously inefficient -> find a good middle ground between the two


class InstantConfigAttr:
    """A descriptor that looks up and saves the values from/to the user config"""

    def __init__(self, default):
        self._default = default
        self._conf_path = user_config_path()

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, type):
        value = dotenv.get_key(self._conf_path, self._name)
        return ast.literal_eval(value) if value is not None else self._default

    def __set__(self, obj, value):
        dotenv.set_key(user_config_path(), self._name, repr(value), quote_mode="auto")


class Config:
    dirs_first = InstantConfigAttr(True)
    order_case_sensitive = InstantConfigAttr(True)
    show_hidden = InstantConfigAttr(False)
    theme = InstantConfigAttr("textual-dark")
    bookmarks = InstantConfigAttr([str(Path.home())])
    file_systems = InstantConfigAttr([])


config = Config()


def user_has_accepted_license():
    """Whether user has accepted the license or not yet"""
    return (config_root() / "user_has_accepted_license").is_file()


def set_user_has_accepted_license():
    (config_root() / "user_has_accepted_license").touch()
