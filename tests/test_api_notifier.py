from unittest.mock import Mock, patch

from job_alert.models import Job
from job_alert.notifier import AlertApiNotifier


@patch("job_alert.notifier.requests.post")
def test_api_notifier_submits_normalized_job(post: Mock) -> None:
    post.return_value.raise_for_status.return_value = None
    AlertApiNotifier("https://api.example.test/", "secret", 12).send(
        Job("42", "Data Analyst", location="Albany", url="https://jobs.example.test/42")
    )
    assert post.call_args.args[0] == "https://api.example.test/api/jobs"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"
    assert post.call_args.kwargs["json"]["job_id"] == "42"
