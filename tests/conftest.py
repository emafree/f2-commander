import shutil

import pytest

from .f2pilot import create_app, create_sample_fs


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def sample_fs():
    fs = create_sample_fs()
    yield fs
    shutil.rmtree(fs.as_posix())
