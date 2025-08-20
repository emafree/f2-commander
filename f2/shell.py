# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import os
import platform
import shlex
import shutil
from typing import Optional


def default_editor() -> Optional[str]:
    """Try to find an editor. Returns a command as a splitted list of arguments,
    or None if no viable alternative is found. Prefers $EDITOR when possible."""

    editor = os.getenv("EDITOR")
    if editor:
        parts = shlex.split(editor)
        if shutil.which(parts[0]):
            return editor

    for cmd in ("vi", "nano", "edit"):
        if shutil.which(cmd):
            return cmd

    return None


def default_viewer(or_editor: bool = True) -> Optional[str]:
    """Try to find a viewer. Returns a command as a splitted list of arguments,
    or None if no viable alternative is found. Use editor if no viewer is found."""

    for cmd in ("less", "more"):
        if shutil.which(cmd):
            return cmd

    return default_editor() if or_editor else None


def default_shell() -> Optional[str]:
    """Try to find a shell executable. Returns a command as a splitted list of
    arguments, or None if no viable alternative is found."""

    for cmd in ("zsh", "fish", "bash", "sh", "powershell.ext", "cmd.exe"):
        if shutil.which(cmd):
            return cmd

    return None


def native_open() -> Optional[str]:
    """Returns a generic 'file opener' relevant for the current OS, or None if none
    is known for the use OS."""

    os_family = platform.system()
    if os_family == "Linux":
        return "xdg-open"
    elif os_family == "Darwin":
        return "open"
    elif os_family == "Windows":
        return "start"
    else:
        return None
