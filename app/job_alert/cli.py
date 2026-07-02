"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
import time

from .client import StateJobsClient
from .config import load_config
from .exceptions import JobAlertError
from .logging_config import configure_logging
from .notifier import EmailNotifier
from .service import JobAlertService
from .storage import SeenJobStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor StateJobsNY and email new matches")
    parser.add_argument("--config", default="config/config.yaml", help="YAML configuration path")
    args = parser.parse_args(argv)
    started = time.monotonic()
    try:
        config = load_config(args.config)
        configure_logging(config.log_directory, config.log_level)
        logger = logging.getLogger(__name__)
        logger.info("NY State job alert run started")
        service = JobAlertService(
            config,
            StateJobsClient(config.http),
            SeenJobStore(config.state_file),
            EmailNotifier(config.smtp, config.template_file),
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

