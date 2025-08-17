# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path

import platformdirs

from .widgets.dialogs import StaticDialog


def log_dir() -> Path:
    return Path(platformdirs.user_log_dir("f2commander"))


def log_uncaught_error(debug_enabled: bool):
    if not debug_enabled:
        return

    log_file = log_dir() / "uncaught_errors.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 50}\n")
        f.write(f"Exception occurred at: {datetime.now()}\n")
        f.write(f"{'=' * 50}\n")
        f.write(traceback.format_exc())
        f.write(f"\n{'=' * 50}\n\n")


def with_error_handler(app):
    """
    Decorator that catches all exceptions and displays an error dialog.
    """

    def wrapper(fn):
        @wraps(fn)
        def impl(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                log_uncaught_error(debug_enabled=app.f2_app_debug)
                app.push_screen(
                    StaticDialog.error("Error", str(e)),
                    lambda _: app.refresh(),
                )
                return None

        return impl

    return wrapper


@asynccontextmanager
async def error_handler_async(app):
    """
    Context manager that catches all exceptions and displays an error dialog.
    """

    try:
        yield
    except Exception as e:
        log_uncaught_error(debug_enabled=app.f2_app_debug)
        await app.push_screen_wait(StaticDialog.error("Error", str(e)))
        app.refresh()
