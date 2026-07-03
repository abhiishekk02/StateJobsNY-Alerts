"""Secure HTML email rendering and SMTP delivery."""

from __future__ import annotations

import smtplib
import requests
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .config import SmtpConfig
from .exceptions import NotificationError
from .models import Job

SUBJECT = "🚨 New NY State Job Match Found"


class EmailNotifier:
    """Render and send one alert through authenticated SMTP."""

    def __init__(self, config: SmtpConfig, template_file: Path) -> None:
        self.config = config
        try:
            environment = Environment(
                loader=FileSystemLoader(str(template_file.parent or Path("."))),
                autoescape=select_autoescape(("html", "xml")),
                undefined=StrictUndefined,
            )
            self.template = environment.get_template(template_file.name)
        except Exception as exc:
            raise NotificationError(f"Cannot load email template {template_file}: {exc}") from exc

    def create_message(self, job: Job, generated_at: datetime | None = None) -> EmailMessage:
        generated_at = generated_at or datetime.now(timezone.utc)
        message = EmailMessage()
        message["Subject"] = SUBJECT
        message["From"] = self.config.username
        message["To"] = self.config.recipient
        message.set_content(
            f"New NY State job: {job.title}\n{job.agency}\n{job.location}\n{job.url}"
        )
        message.add_alternative(
            self.template.render(job=job, generated_at=generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            subtype="html",
        )
        return message

    def send(self, job: Job) -> None:
        message = self.create_message(job)
        try:
            with smtplib.SMTP(
                self.config.server, self.config.port, timeout=self.config.timeout_seconds
            ) as smtp:
                smtp.ehlo()
                if self.config.use_starttls:
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(self.config.username, self.config.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise NotificationError(f"Could not email vacancy {job.job_id}: {exc}") from exc


class AlertApiNotifier:
    """Submit normalized jobs to the private subscriber delivery API."""

    broad_search = True

    def __init__(self, api_url: str, api_key: str, timeout_seconds: float) -> None:
        self.url = f"{api_url.rstrip('/')}/api/jobs"
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def send(self, job: Job) -> None:
        try:
            response = requests.post(
                self.url,
                json={
                    "job_id": job.job_id,
                    "title": job.title,
                    "agency": job.agency,
                    "grade": job.grade,
                    "salary": job.salary,
                    "employment_type": job.employment_type,
                    "location": job.location,
                    "posting_date": job.posting_date,
                    "deadline": job.deadline,
                    "url": job.url,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise NotificationError(f"Could not deliver vacancy {job.job_id} to alert API: {exc}") from exc
