# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, Optional

import platformdirs
import pydantic


class ConfigError(Exception):
    pass


#
# CONFIG MODEL (and default configuration values)
#


class Display(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    dirs_first: bool = True
    order_case_sensitive: bool = True
    show_hidden: bool = False
    theme: str = "textual-dark"


class Bookmarks(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    paths: list[str] = [
        "~",
        f"~/{Path(platformdirs.user_documents_dir()).relative_to(Path.home())}",
        f"~/{Path(platformdirs.user_downloads_dir()).relative_to(Path.home())}",
        f"~/{Path(platformdirs.user_pictures_dir()).relative_to(Path.home())}",
        f"~/{Path(platformdirs.user_videos_dir()).relative_to(Path.home())}",
        f"~/{Path(platformdirs.user_music_dir()).relative_to(Path.home())}",
    ]


class FileSystem(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    display_name: str
    protocol: str
    path: str = ""
    params: dict[str, Any]


class Startup(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    license_accepted: bool = False

    check_for_updates: bool = True
    last_update_check_time: int = 0
    last_update_check_version: str = "0"


class System(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    ask_before_quit: bool = True
    editor: Optional[str] = None
    viewer: Optional[str] = None
    shell: Optional[str] = None


class Config(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

    keymap: Literal["vi", "fn"] = "vi"
    display: Display = Display()
    bookmarks: Bookmarks = Bookmarks()
    file_systems: list[FileSystem] = [
        FileSystem(
            display_name="Rebex.net Demo FTP server",
            protocol="ftp",
            params={
                "host": "test.rebex.net",
                "username": "demo",
                "password": "password",
            },
        )
    ]
    startup: Startup = Startup()
    system: System = System()


#
# AUTOSAVE
#


class ConfigWithAutosave(Config):
    _config_path: Path

    def __init__(self, config_path, config):
        super().__init__(**config.model_dump())
        self._config_path = config_path

    @contextmanager
    def autosave(self):
        before = self.model_dump_json(indent=2)
        yield self
        after = self.model_dump_json(indent=2)
        if before != after:
            self._config_path.write_text(after)


#
# USER-LEVEL CONFIG ENTRY POINT
#


def config_root() -> Path:
    """Path to the directory that hosts all configuration files"""
    root_dir = platformdirs.user_config_path("f2commander")
    if not root_dir.exists():
        root_dir.mkdir(parents=True)
    return root_dir


def user_config_path() -> Path:
    """Path to the file with user's application config"""
    return config_root() / "config.json"


def user_config(config_path: Path):
    """
    Loads and parses user's configuration file and returns a Config instance that
    can also automatically save changes made within the autosave() context.
    """
    if not config_path.exists():
        config_path.write_text(Config().model_dump_json(indent=2))

    try:
        config = Config.model_validate_json(config_path.read_text())
        with_autosave = ConfigWithAutosave(config_path, config)
        return with_autosave
    except pydantic.ValidationError as err:
        msg = err.json(include_input=False, include_url=False, include_context=False)
        raise ConfigError(msg)
