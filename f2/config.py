# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2025 Timur Rubeko

import ast
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import dotenv
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


class Config(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(validate_assignment=True)

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
# BACKWARD COMPATIBILITY WITH OLD .ENV CONFIG
#


def migrate_legacy_config():
    config_path = user_config_path()
    if config_path.is_file():
        # default configuration file already exists, do not change it
        return

    dotenv_path = config_root() / "user.env"
    if not dotenv_path.is_file():
        # legacy configuration file is not found, nothing to migrate
        return

    license_accepted_path = config_root() / "user_has_accepted_license"

    legacy_config = dotenv.dotenv_values(dotenv_path)

    config = Config()
    if "dirs_first" in legacy_config:
        config.display.dirs_first = legacy_config["dirs_first"]
    if "order_case_sensitive" in legacy_config:
        config.display.order_case_sensitive = legacy_config["order_case_sensitive"]
    if "show_hidden" in legacy_config:
        config.display.show_hidden = legacy_config["show_hidden"]
    if "theme" in legacy_config:
        config.display.theme = ast.literal_eval(legacy_config["theme"])
    if "bookmarks" in legacy_config:
        config.bookmarks.paths = ast.literal_eval(legacy_config["bookmarks"])
    if "file_systems" in legacy_config:
        config.file_systems = []
        legacy_file_systems = ast.literal_eval(legacy_config.get("file_systems"))
        for legacy_fs in legacy_file_systems:
            if "display_name" not in legacy_fs or "protocol" not in legacy_fs:
                continue
            fs = FileSystem(
                display_name=legacy_fs["display_name"],
                protocol=legacy_fs["protocol"],
                path=legacy_fs.get("path", ""),
                params={
                    k: v
                    for k, v in legacy_fs.items()
                    if k not in ("display_name", "protocol", "path")
                },
            )
            config.file_systems.append(fs)
    config.startup.license_accepted = license_accepted_path.is_file()

    config_path.write_text(config.model_dump_json(indent=2))

    dotenv_path.rename(f"{dotenv_path}.bak")
    if license_accepted_path.is_file():
        license_accepted_path.unlink()


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
