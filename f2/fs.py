# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import fnmatch
import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from fsspec import AbstractFileSystem, filesystem


@dataclass
class DirList:
    file_count: int
    dir_count: int
    total_size: int
    entries: list["DirEntry"]


@dataclass
class DirEntry:
    name: str
    size: int
    mtime: float
    is_file: bool
    is_dir: bool
    is_link: bool
    is_hidden: bool
    is_executable: bool

    @classmethod
    def from_path(cls, fs: AbstractFileSystem, path: Path) -> "DirEntry":
        info = fs.info(path.as_posix())
        return DirEntry(
            name=path.name,
            size=info.get("size") or fs.size(path),
            mtime=_find_mtime(info),
            is_dir=info.get("type") == "directory",
            is_file=info.get("type") == "file",
            is_link=info.get("islink", False),
            is_hidden=_is_hidden(info),
            is_executable=_is_executable(info),
        )


def _find_mtime(info: dict[str, Any]):
    value = info.get("mtime", info.get("updated"))
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if isinstance(value, datetime):
        value = value.timestamp()
    return value


def _is_hidden(info: dict[str, Any]) -> bool:
    path = Path(info["name"])
    return path.name.startswith(".") or _is_local_file_hidden(path)


def _is_local_file_hidden(path: Path) -> bool:
    if not path.exists():
        return False

    statinfo = path.lstat()
    return _has_hidden_attribute(statinfo) or _has_hidden_flag(statinfo)


def _has_hidden_attribute(statinfo: os.stat_result) -> bool:
    if not hasattr(statinfo, "st_file_attributes"):
        return False
    if not hasattr(stat, "FILE_ATTRIBUTE_HIDDEN"):
        return False
    return bool(
        statinfo.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN  # type: ignore
    )


def _has_hidden_flag(statinfo: os.stat_result) -> bool:
    if not hasattr(stat, "UF_HIDDEN") or not hasattr(statinfo, "st_flags"):
        return False
    return bool(statinfo.st_flags & stat.UF_HIDDEN)  # type: ignore


def _is_executable(statinfo: dict[str, Any]) -> bool:
    if "mode" not in statinfo:
        return False

    mode = statinfo["mode"]
    return stat.S_ISREG(mode) and bool(mode & stat.S_IXUSR)


def list_dir(
    fs: AbstractFileSystem,
    path: Path,
    include_up_dir: bool = True,
    include_hidden: bool = True,
    glob_expression: str | None = None,
) -> DirList:
    if not path.is_dir():
        raise ValueError(f"{path} is not a directory")

    total_size = 0
    file_count = 0
    dir_count = 0
    entries = []

    if include_up_dir and path.parent != path:
        up = DirEntry.from_path(fs, path)
        up.name = ".."
        entries.append(up)

    for child in fs.ls(path.as_posix()):
        entry = DirEntry.from_path(fs, Path(child))
        if glob_expression and not fnmatch.fnmatch(entry.name, glob_expression):
            continue
        if entry.is_hidden and not include_hidden:
            continue
        entries.append(entry)
        total_size += entry.size
        if entry.is_file:
            file_count += 1
        elif entry.is_dir:
            dir_count += 1

    return DirList(
        file_count=file_count,
        dir_count=dir_count,
        total_size=total_size,
        entries=entries,
    )


def breadth_first_walk(path: Path, include_hidden: bool = True) -> Iterator[Path]:

    fs = filesystem("file")  # TODO: support other filesystems

    dirs_to_walk = [path]
    while dirs_to_walk:
        next_dirs_to_walk = []
        for d in dirs_to_walk:
            for p in fs.ls(d.as_posix()):
                info = fs.info(path.as_posix())
                if _is_hidden(info) and not include_hidden:
                    continue
                if p.is_dir():
                    next_dirs_to_walk.append(p)
                yield p
        dirs_to_walk = next_dirs_to_walk
