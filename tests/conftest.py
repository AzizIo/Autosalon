import shutil
from pathlib import Path

import pytest


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'AutoSalon.db'
    target = tmp_path / 'AutoSalon_test.db'
    shutil.copy2(source, target)
    from models import data_access
    monkeypatch.setattr(data_access, 'DB_PATH', str(target))
    return target
