"""Console and rotating-file logging."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(directory: Path, level: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / "job_alert.log"
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s", "%Y-%m-%dT%H:%M:%S%z"
    )
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(console)
    root.addHandler(file_handler)
    return log_file

