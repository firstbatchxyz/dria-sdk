import os
import inspect


def _get_abs_path(path: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, path)


def get_abs_path(path: str):
    caller_frame = inspect.stack()[1]
    caller_filename = caller_frame.filename
    caller_dir = os.path.dirname(os.path.abspath(caller_filename))
    return os.path.join(caller_dir, path)
