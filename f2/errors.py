# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

from contextlib import asynccontextmanager
from functools import wraps

from .widgets.dialogs import StaticDialog


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
        await app.push_screen_wait(StaticDialog.error("Error", str(e)))
        app.refresh()
