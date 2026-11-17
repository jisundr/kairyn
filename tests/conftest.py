import pytest

from helpers import make_good_repo


@pytest.fixture
def good_repo(tmp_path):
    return make_good_repo(tmp_path / "repo")
