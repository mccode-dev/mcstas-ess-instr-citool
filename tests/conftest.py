import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "example_repos"
EXAMPLES = sorted(p.name for p in EXAMPLES_DIR.iterdir() if p.is_dir())


@pytest.fixture
def copy_example(tmp_path):
    """Returns a function which copies an example project into tmp_path."""
    def _copy(name, dest_name=None):
        dest = tmp_path / (dest_name or name)
        shutil.copytree(EXAMPLES_DIR / name, dest,
                        ignore=shutil.ignore_patterns("__pycache__"))
        return dest
    return _copy
