"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

from .client import StateJobsClient
from .config import load_config
from .exceptions import JobAlertError
from .logging_config import configure_logging
from .notifier import AlertApiNotifier, EmailNotifier
from .service import JobAlertService
from .storage import SeenJobStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor StateJobsNY and email new matches")
    parser.add_argument("--config", default="config/config.yaml", help="YAML configuration path")
    args = parser.parse_args(argv)
    started = time.monotonic()
    try:
        api_url = os.getenv("ALERT_API_URL", "").strip()
        api_key = os.getenv("ALERT_API_KEY", "").strip()
        config = load_config(args.config, require_email=not api_url)
        configure_logging(config.log_directory, config.log_level)
        logger = logging.getLogger(__name__)
        logger.info("NY State job alert run started")
        if api_url:
            if not api_key:
                raise JobAlertError("ALERT_API_KEY is required when ALERT_API_URL is set")
            notifier = AlertApiNotifier(api_url, api_key, config.http.timeout_seconds)
        else:
            notifier = EmailNotifier(config.smtp, config.template_file)
        service = JobAlertService(
            config,
            StateJobsClient(config.http),
            SeenJobStore(config.state_file),
            notifier,
        )
        stats = service.run()
        logger.info(
            "Run complete: found=%d matched=%d sent=%d already_seen=%d duration=%.2fs",
            stats.found, stats.matched, stats.sent, stats.skipped_seen, time.monotonic() - started,
        )
        return 0
    except JobAlertError as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).error("Job alert run failed: %s", exc)
        return 1
    except Exception:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger(__name__).exception("Unexpected fatal error in job alert run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
