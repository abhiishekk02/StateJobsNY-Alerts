from pathlib import Path

import pytest

from job_alert.config import AppConfig, HttpConfig, SearchConfig, SmtpConfig


@pytest.fixture
def search_config() -> SearchConfig:
    return SearchConfig(
        url="https://example.test/search.cfm",
        results_url="https://example.test/vacancyTable.cfm",
        keywords=("Python", "ITS", "Data Analyst"),
        locations=("Albany",),
        grades=("18",),
        regions=("0",),
    )


@pytest.fixture
def app_config(tmp_path: Path, search_config: SearchConfig) -> AppConfig:
    return AppConfig(
        search=search_config,
        smtp=SmtpConfig("smtp.test", 587, "from@test", "secret", "to@test", True, 10),
        http=HttpConfig(10, 1, 0, "Test/1.0"),
        state_file=tmp_path / "seen.json",
        template_file=Path("templates/job_alert.html"),
        log_directory=tmp_path / "logs",
        log_level="INFO",
        schedule="*/15 * * * *",
    )

