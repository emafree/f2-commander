from functools import wraps

from .widgets.dialogs import StaticDialog, Style


def with_error_handler(app):

    def on_dismiss(_):
        app.refresh()

    def wrapper(fn):

        @wraps(fn)
        def impl(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                app.push_screen(
                    StaticDialog.error(
                        "Error",
                        f"An unexpected error occurred: {e}",
                    ),
                    on_dismiss,
                )
                return None

        return impl

    return wrapper
