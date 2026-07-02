from datetime import datetime, timezone
from pathlib import Path

from job_alert.config import SmtpConfig
from job_alert.models import Job
from job_alert.notifier import EmailNotifier, SUBJECT


def test_email_generation_escapes_untrusted_html(tmp_path: Path) -> None:
    template = tmp_path / "email.html"
    template.write_text("<h1>{{ job.title }}</h1><a href=\"{{ job.url }}\">Open</a>{{ generated_at }}")
    config = SmtpConfig("smtp.test", 587, "sender@test", "x", "recipient@test", True, 10)
    notifier = EmailNotifier(config, template)
    job = Job("1", "<script>alert(1)</script>", url="https://example.test/job")
    message = notifier.create_message(job, datetime(2026, 7, 2, tzinfo=timezone.utc))
    html = message.get_body(preferencelist=("html",)).get_content()
    assert message["Subject"] == SUBJECT
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert message["To"] == "recipient@test"
