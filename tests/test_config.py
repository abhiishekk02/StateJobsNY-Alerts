from pathlib import Path

import pytest

from job_alert.config import load_config
from job_alert.exceptions import ConfigurationError


VALID = """
search:
  url: https://example.test/search
  results_url: https://example.test/results
  keywords: [Python]
  locations: [Albany]
  grades: ['18']
  regions: ['0']
email:
  recipient: user@example.test
  smtp_server: smtp.example.test
  smtp_port: 587
  use_starttls: true
  timeout_seconds: 30
http:
  timeout_seconds: 20
  retry_count: 2
  backoff_seconds: 1
  user_agent: Test/1.0
paths:
  state_file: data/seen.json
  template_file: templates/email.html
  log_directory: logs
logging: {level: INFO}
schedule: '*/15 * * * *'
"""


def test_load_config_and_environment_secrets(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(VALID)
    monkeypatch.setenv("EMAIL_ADDRESS", "sender@gmail.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "app-password")
    config = load_config(path)
    assert config.smtp.username == "sender@gmail.com"
    assert config.search.grades == ("18",)


def test_missing_credentials_are_rejected(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(VALID)
    monkeypatch.delenv("EMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    with pytest.raises(ConfigurationError, match="EMAIL_ADDRESS"):
        load_config(path)


def test_empty_keyword_list_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(VALID.replace("keywords: [Python]", "keywords: []"))
    with pytest.raises(ConfigurationError, match="non-empty"):
        load_config(path, require_email=False)

