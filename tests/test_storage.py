import json

import pytest

from job_alert.exceptions import StorageError
from job_alert.storage import SeenJobStore


def test_store_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "seen.json"
    store = SeenJobStore(path)
    assert not store.contains("42")
    store.mark_sent("42", "Data Analyst")
    assert SeenJobStore(path).contains("42")
    assert json.loads(path.read_text())["jobs"]["42"]["title"] == "Data Analyst"


def test_invalid_state_is_rejected(tmp_path) -> None:
    path = tmp_path / "seen.json"
    path.write_text("not-json")
    with pytest.raises(StorageError, match="Cannot read"):
        SeenJobStore(path)

