import pytest


@pytest.fixture
def isolated_cwd(tmp_path, monkeypatch):
    """Run a test inside an empty temp directory as cwd.

    Anything that resolves paths off Path.cwd() (like runs_dir_for_config)
    will read and write inside tmp_path instead of the real project.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path