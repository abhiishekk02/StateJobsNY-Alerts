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


class BroadClient:
    def __init__(self) -> None:
        self.params = None

    def get(self, url, params=None):
        self.params = params
        return '<p>No vacancies found.</p>'


class BroadNotifier(FakeNotifier):
    broad_search = True


def test_empty_run(app_config) -> None:
    stats = JobAlertService(
        app_config, FakeClient(), SeenJobStore(app_config.state_file), FakeNotifier()
    ).run()
    assert stats.found == stats.matched == stats.sent == 0


def test_subscriber_mode_searches_all_grades_and_regions(app_config) -> None:
    client = BroadClient()
    JobAlertService(
        app_config, client, SeenJobStore(app_config.state_file), BroadNotifier()
    ).run()
    assert client.params == {"searchResults": "Yes"}
