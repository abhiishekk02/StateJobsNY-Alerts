"""Secure HTML email rendering and SMTP delivery."""

from __future__ import annotations

import smtplib
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
