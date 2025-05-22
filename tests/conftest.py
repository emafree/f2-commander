import shutil
import tempfile
from pathlib import Path
from typing import Optional

import pytest

from f2.app import F2Commander


@pytest.fixture
def app():
    app = F2Commander()
    return app


def _touch(path: Path, size: Optional[int], content: Optional[bytes] = None):
    assert (
        size is not None or content is not None
    ), "Either size or content must be provided"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        if content is not None:
            f.write(content)
        else:
            f.write(b"." * size)


@pytest.fixture
def sample_fs():
    # Create a temporary directory to host the sample FS
    sample_fs_path = tempfile.mkdtemp()
    fs = Path(sample_fs_path)

    # Fill in the sample directory with content...
    # home directory:
    _touch(fs / "todo.md", size=5000)
    _touch(fs / ".bashrc", size=373)
    _touch(fs / ".profile", size=125)
    _touch(fs / "notes.txt", size=10000)
    _touch(fs / "contacts.csv", size=3000)
    _touch(fs / "settings.json", size=1500)
    _touch(fs / "backup.zip", size=20000)
    _touch(fs / "credentials.txt", size=733)
    _touch(fs / "update.sh", size=2500)
    (fs / "update.sh").chmod(mode=0o744)
    # Documents:
    _touch(fs / "Documents/Work/Reports/quarterly_report.docx", size=12000)
    _touch(fs / "Documents/Work/summary.txt", size=1200)
    _touch(fs / "Documents/Personal/Finances/budget_2024.xlsx", size=24000)
    _touch(fs / "Documents/Personal/expenses.csv", size=2400)
    # Downloads:
    _touch(fs / "Downloads/project_archive.zip", size=10000)
    _touch(fs / "Downloads/old_documents.tar.gz", size=20000)
    # Pictures:
    _touch(fs / "Pictures/Vacations/2023/beach.jpg", size=10000)
    _touch(fs / "Pictures/Vacations/2023/mountains.png", size=12000)
    _touch(fs / "Pictures/Family/family_reunion.jpg", size=9000)
    (fs / "Photos").symlink_to(fs / "Pictures")
    # Music:
    _touch(fs / "Music/Playlists/favorites.m3u", size=1000)
    _touch(fs / "Music/workout.mp3", size=20000)
    # Videos:
    _touch(fs / "Videos/Movies/saved_film.mp4", size=100000)
    # Projects:
    _touch(fs / "Projects/Web/index.html", size=2000)
    _touch(fs / "Projects/Web/styles.css", size=1000)
    _touch(fs / "Projects/Mobile/app.js", size=4000)
    # Templates:
    (fs / "Templates").mkdir()

    yield fs

    # Cleanup
    shutil.rmtree(sample_fs_path)
