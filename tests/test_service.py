from job_alert.models import Job
from job_alert.service import JobAlertService
from job_alert.storage import SeenJobStore


class FakeClient:
    def get(self, url, params=None):
        if "vacancyTable" in url:
            return '<p>No vacancies found.</p>'
        raise AssertionError("unexpected detail request")


class FakeNotifier:
    def send(self, job: Job) -> None:
        raise AssertionError("unexpected email")


def test_empty_run(app_config) -> None:
    stats = JobAlertService(
        app_config, FakeClient(), SeenJobStore(app_config.state_file), FakeNotifier()
    ).run()
    assert stats.found == stats.matched == stats.sent == 0
