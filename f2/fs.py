# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import fnmatch
import mimetypes
import os
import posixpath
import shutil
import stat
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

import libarchive
from fsspec import AbstractFileSystem
from fsspec.implementations.libarchive import LibArchiveFileSystem
from fsspec.implementations.zip import ZipFileSystem

ZIP_MIMETYPES = [
    "application/zip",
]

LIBARCHIVE_MIMETYPES = [
    # Standard archive formats
    "application/x-tar",
    "application/zip",
    "application/x-cpio",
    "application/x-archive",
    "application/x-shar",
    "application/x-iso9660-image",
    "application/x-pax",
    # Compressed formats
    "application/gzip",
    "application/x-gzip",
    "application/x-bzip2",
    "application/x-xz",
    "application/x-lzip",
    "application/x-lzma",
    "application/x-lzop",
    "application/x-compress",
    "application/zstd",
    # Compressed tar formats
    "application/x-compressed-tar",  # .tar.gz
    "application/x-bzip2-compressed-tar",  # .tar.bz2
    "application/x-xz-compressed-tar",  # .tar.xz
    "application/x-lzip-compressed-tar",  # .tar.lz
    "application/x-lzma-compressed-tar",  # .tar.lzma
    "application/x-lzop-compressed-tar",  # .tar.lzo
    "application/x-tarz",  # .tar.Z
    "application/x-zstd-compressed-tar",  # .tar.zst
    # 7-Zip formats
    "application/x-7z-compressed",
    # RAR formats
    "application/vnd.rar",
    "application/x-rar-compressed",
    # Microsoft formats
    "application/vnd.ms-cab-compressed",
    "application/x-msi",
    # Mac formats
    "application/x-apple-diskimage",
    "application/x-xar",
    # Package formats
    "application/x-rpm",
    "application/x-debian-package",
    # Less common formats
    "application/x-mtree",
    "application/warc",
    "application/x-lha",
    "application/warc",
    # Disk images
    "application/x-raw-disk-image",
    "application/x-cd-image",
    # Generic binary
    # "application/octet-stream",
]

LIBARCHIVE_READ_EXTENSIONS = [
    ".xar",
    ".pax",
    ".warc",
]

LIBARCHIVE_WRITE_EXTENSIONS = {
    ".tar": ("gnutar", None),
    ".tar.gz": ("gnutar", "gzip"),
    ".tgz": ("gnutar", "gzip"),
    ".tar.bz2": ("gnutar", "bzip2"),
    ".tbz2": ("gnutar", "bzip2"),
    ".tar.xz": ("gnutar", "xz"),
    ".txz": ("gnutar", "xz"),
    ".zip": ("zip", None),
    ".ar": ("ar_bsd", None),
    # ".shar": ("shar", None),
    ".xar": ("xar", None),
    ".cpio": ("cpio", None),
    ".pax": ("pax", None),
    ".warc": ("warc", None),
    ".7z": ("7zip", None),
}


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
    is_archive: bool = False

    @classmethod
    def from_info(cls, fs: AbstractFileSystem, info: dict[str, Any]) -> "DirEntry":
        return DirEntry(
            name=posixpath.basename(info["name"]),
            size=int(info.get("size") or 0),
            mtime=_find_mtime(info),
            is_dir=info.get("type") == "directory",
            is_file=info.get("type") == "file",
            is_link=info.get("islink", False),
            is_hidden=_is_hidden(info),
            is_executable=is_executable(info),
            is_archive=is_supported_archive(info["name"]),
        )


def _find_mtime(info: dict[str, Any]) -> float:
    # search for various mtime-like attributes:
    fs_mtime = None
    for name in (
        "mtime",
        "updated",
        "LastModified",
        "last_modified",
        "modify",
        "date_time",
    ):
        if name in info:
            fs_mtime = info[name]
            break

    mtime: Optional[float] = None

    # try to convert the value found:
    if isinstance(fs_mtime, str):
        try:
            mtime = datetime.fromisoformat(fs_mtime).timestamp()
        except ValueError:
            try:
                mtime = datetime.strptime(fs_mtime, "%Y%m%d%H%M%S").timestamp()
            except ValueError:
                pass
    elif isinstance(fs_mtime, datetime):
        mtime = fs_mtime.timestamp()
    elif isinstance(fs_mtime, tuple) and len(fs_mtime) == 6:
        mtime = datetime(*fs_mtime).timestamp()
    elif isinstance(fs_mtime, int):
        mtime = float(fs_mtime)
    elif isinstance(fs_mtime, float):
        mtime = fs_mtime

    # if could not find or convert, use a default value:
    if mtime is None:
        mtime = datetime(1970, 1, 1).timestamp()

    return mtime


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
    glob_expression: Optional[str] = None,
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


def copy(src_fs: AbstractFileSystem, src: str, dst_fs: AbstractFileSystem, dst: str):
    """Copy file or directory in the same or between different file systems"""
    if src_fs == dst_fs:  # same file system (both local or both same remote)
        src_fs.copy(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
    elif is_local_fs(src_fs):  # upload to remote
        dst_fs.put(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
    elif is_local_fs(dst_fs):  # download from remote
        src_fs.get(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
    else:  # distinct remote file systems: download and upload
        tmp_dir_path = tempfile.mkdtemp(prefix=f"{posixpath.basename(src)}.")
        try:
            src_fs.get(
                src,
                tmp_dir_path + "/",
                recursive=src_fs.isdir(src),
                on_error="raise",
            )
            dst_fs.put(
                posixpath.join(tmp_dir_path, os.path.basename(src)),
                dst,
                recursive=src_fs.isdir(src),
                on_error="raise",
            )
        finally:
            shutil.rmtree(tmp_dir_path)


def move(src_fs: AbstractFileSystem, src: str, dst_fs: AbstractFileSystem, dst: str):

    # Following code exists because fsspec may use strip_protocol on the path
    # removing the trailing slash and thus changing the semantics of `move`;
    # all would work as expected, except that non-existing target dir names
    # would not be used as the destination instead.
    if dst.endswith("/") and not dst_fs.isdir(dst):
        raise ValueError(f"No such directory: {dst}")

    if src_fs == dst_fs:  # same file system (both local or both same remote)
        src_fs.move(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
    elif is_local_fs(src_fs):  # upload to remote
        dst_fs.put(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
        src_fs.rm(src, recursive=src_fs.isdir(src))
    elif is_local_fs(dst_fs):  # download from remote
        src_fs.get(
            src,
            dst,
            recursive=src_fs.isdir(src),
            on_error="raise",
        )
        src_fs.rm(src, recursive=src_fs.isdir(src))
    else:  # distinct remote file systems: download and upload
        tmp_dir_path = tempfile.mkdtemp(prefix=f"{posixpath.basename(src)}.")
        try:
            src_fs.get(
                src,
                tmp_dir_path + "/",
                recursive=src_fs.isdir(src),
                on_error="raise",
            )
            dst_fs.put(
                posixpath.join(tmp_dir_path, os.path.basename(src)),
                dst,
                recursive=src_fs.isdir(src),
                on_error="raise",
            )
            src_fs.rm(src, recursive=src_fs.isdir(src))
        finally:
            shutil.rmtree(tmp_dir_path)


def is_local_fs(fs: AbstractFileSystem) -> bool:
    return "file" in fs.protocol


def is_archive_fs(fs: AbstractFileSystem) -> bool:
    return isinstance(fs, LibArchiveFileSystem) or isinstance(fs, ZipFileSystem)


def is_supported_archive(path: str) -> bool:
    _, ext = posixpath.splitext(path)
    mime_type = mimetypes.guess_type(path)[0]
    return (
        mime_type in ZIP_MIMETYPES
        or mime_type in LIBARCHIVE_MIMETYPES
        or ext in LIBARCHIVE_READ_EXTENSIONS  # some mime types are not recognized
    )


def open_archive(path: str) -> Optional[LibArchiveFileSystem]:

    def _try_open(impl):
        try:
            archive_fs = impl(path, mode="r")
            archive_fs.ls("")
            return archive_fs
        except Exception:
            return None

    archive_fs = None
    if mimetypes.guess_type(path)[0] in ZIP_MIMETYPES:
        archive_fs = _try_open(ZipFileSystem)
    elif LibArchiveFileSystem:
        archive_fs = _try_open(LibArchiveFileSystem)
    return archive_fs


def write_archive(inputs: list[str], relative_to: str, output: str):
    matching_ext = [m for m in LIBARCHIVE_WRITE_EXTENSIONS if output.endswith(m)]
    if not matching_ext:
        _, ext = posixpath.splitext(output)
        raise ValueError(f"Unsupported archive format: `{ext}`")

    ext = matching_ext[0]
    fmt, compression = LIBARCHIVE_WRITE_EXTENSIONS[ext]

    rel_paths = [os.path.relpath(p, relative_to) for p in inputs]
    cwd = os.getcwd()
    os.chdir(relative_to)
    try:
        with libarchive.file_writer(output, fmt, compression) as archive:
            archive.add_files(*rel_paths)
    finally:
        os.chdir(cwd)
