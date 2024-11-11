# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import fnmatch
import os
import posixpath
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from fsspec import AbstractFileSystem


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
    def from_info(cls, fs: AbstractFileSystem, info: dict[str, Any]) -> "DirEntry":
        return DirEntry(
            name=posixpath.basename(info["name"]),
            size=int(info.get("size", 0)),
            mtime=_find_mtime(info),
            is_dir=info.get("type") == "directory",
            is_file=info.get("type") == "file",
            is_link=info.get("islink", False),
            is_hidden=_is_hidden(info),
            is_executable=is_executable(info),
        )


def _find_mtime(info: dict[str, Any]) -> float:
    value = None
    for name in ("mtime", "updated", "LastModified", "last_modified"):
        if name in info:
            value = info.get(name)
            break

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            value = None

    if isinstance(value, datetime):
        value = value.timestamp()

    return value


def _is_hidden(info: dict[str, Any]) -> bool:
    path = info["name"]
    return posixpath.basename(path).startswith(".") or _is_local_file_hidden(path)


def _is_local_file_hidden(path: str) -> bool:
    p = Path(path)

    if not p.exists():
        return False

    statinfo = p.lstat()
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


def is_executable(statinfo: dict[str, Any]) -> bool:
    if "mode" not in statinfo:
        return False

    mode = statinfo["mode"]
    return stat.S_ISREG(mode) and bool(mode & stat.S_IXUSR)


def list_dir(
    fs: AbstractFileSystem,
    path: str,
    include_hidden: bool = True,
    glob_expression: str | None = None,
) -> DirList:
    if not fs.isdir(path):
        raise ValueError(f"{path} is not a directory")

    total_size = 0
    file_count = 0
    dir_count = 0
    entries = []

    if posixpath.dirname(path) != path:
        up = DirEntry.from_info(fs, fs.info(path))
        up.name = ".."
        entries.append(up)

    # FIXME: allow ".." when at the root of an archive

    for child in fs.ls(path, detail=True):
        entry = DirEntry.from_info(fs, child)
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


def breadth_first_walk(
    fs: AbstractFileSystem, path: str, include_hidden: bool = True
) -> Iterator[str]:
    dirs_to_walk = [path]
    while dirs_to_walk:
        next_dirs_to_walk = []
        for d in dirs_to_walk:
            for info in fs.ls(d, detail=True):
                p = info["name"]
                if _is_hidden(info) and not include_hidden:
                    continue
                if info.get("type") == "directory":
                    next_dirs_to_walk.append(p)
                yield p
        dirs_to_walk = next_dirs_to_walk


def is_local_fs(fs: AbstractFileSystem) -> bool:
    return "file" in fs.protocol


def is_supported_archive(path: str) -> bool:
    # FIXME: should this use mime types of attempt opening a file?
    supported_extensions = (
        ".zip",
        # TODO: enable libarchive
        # ".tar",
        # ".tar.gz",
        # ".tgz",
        # ".tar.bz2",
        # ".tbz2",
        # ".tar.xz",
        # ".txz",
    )
    return posixpath.splitext(path)[1].lower() in supported_extensions
