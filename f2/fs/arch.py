# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

"""
Routines for working with archives.

Does not use the Node abstraction on purpose, uses lower-level APIs only.
"""

import mimetypes
import os
import posixpath
from typing import Optional

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


class NormArchFileSystem:
    """
    Archive file systems' `.get` behavior differs from that of remote file
    system implementations: it expects the target path to be a non-existing path
    that corresponds to the final name of a file or a directory to be extracted.
    """

    def get(self, rpath: str, lpath: str, *args, **kwargs):
        if os.path.isdir(lpath):
            lpath = os.path.join(lpath, os.path.basename(rpath))
        super().get(rpath, lpath, *args, **kwargs)  # type: ignore


class NormZipFileSystem(NormArchFileSystem, ZipFileSystem):
    pass


class NormLibArchiveFileSystem(NormArchFileSystem, LibArchiveFileSystem):
    pass


def is_archive_fs(fs: AbstractFileSystem) -> bool:
    return isinstance(fs, NormLibArchiveFileSystem) or isinstance(fs, NormZipFileSystem)


def is_archive(path: str) -> bool:
    _, ext = posixpath.splitext(path)
    mime_type = mimetypes.guess_type(path)[0]
    return (
        mime_type in ZIP_MIMETYPES
        or mime_type in LIBARCHIVE_MIMETYPES
        or ext in LIBARCHIVE_READ_EXTENSIONS  # some mime types are not recognized
    )


def open_archive(path: str) -> Optional[AbstractFileSystem]:
    def _try_open(impl):
        try:
            archive_fs = impl(path, mode="r")
            archive_fs.ls("")
            return archive_fs
        except Exception:
            return None

    archive_fs = None
    if mimetypes.guess_type(path)[0] in ZIP_MIMETYPES:
        archive_fs = _try_open(NormZipFileSystem)
    else:
        archive_fs = _try_open(NormLibArchiveFileSystem)
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
