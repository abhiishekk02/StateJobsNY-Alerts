"""Typed configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .exceptions import ConfigurationError


@dataclass(frozen=True)
class SearchConfig:
    url: str
    results_url: str
    keywords: tuple[str, ...]
    locations: tuple[str, ...]
    grades: tuple[str, ...]
    regions: tuple[str, ...]


@dataclass(frozen=True)
class SmtpConfig:
    server: str
    port: int
    username: str
    password: str
    recipient: str
    use_starttls: bool
    timeout_seconds: float


@dataclass(frozen=True)
class HttpConfig:
    timeout_seconds: float
    retry_count: int
    backoff_seconds: float
    user_agent: str


@dataclass(frozen=True)
class AppConfig:
    search: SearchConfig
    smtp: SmtpConfig
    http: HttpConfig
    state_file: Path
    template_file: Path
    log_directory: Path
    log_level: str
    schedule: str


def _need(mapping: dict[str, Any], key: str, section: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise ConfigurationError(f"Missing configuration value: {section}.{key}")
    return value


def _strings(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x.strip() for x in value):
        raise ConfigurationError(f"{name} must be a non-empty list of strings")
    return tuple(x.strip() for x in value)


def load_config(path: str | Path = "config/config.yaml", *, require_email: bool = True) -> AppConfig:
    """Load YAML and secrets from environment variables, then validate them."""
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Cannot read {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration root must be a mapping")

    try:
        search = raw["search"]
        email = raw["email"]
        http = raw["http"]
        paths = raw["paths"]
        smtp = SmtpConfig(
            server=os.getenv("SMTP_SERVER", str(email["smtp_server"])),
            port=int(os.getenv("SMTP_PORT", email["smtp_port"])),
            username=os.getenv("EMAIL_ADDRESS", ""),
            password=os.getenv("EMAIL_PASSWORD", ""),
            recipient=os.getenv("EMAIL_RECIPIENT", str(email["recipient"])),
            use_starttls=bool(email["use_starttls"]),
            timeout_seconds=float(email["timeout_seconds"]),
        )
        result = AppConfig(
            search=SearchConfig(
                url=str(_need(search, "url", "search")),
                results_url=str(_need(search, "results_url", "search")),
                keywords=_strings(search["keywords"], "search.keywords"),
                locations=_strings(search["locations"], "search.locations"),
                grades=_strings(search["grades"], "search.grades"),
                regions=_strings(search["regions"], "search.regions"),
            ),
            smtp=smtp,
            http=HttpConfig(
                timeout_seconds=float(http["timeout_seconds"]),
                retry_count=int(http["retry_count"]),
                backoff_seconds=float(http["backoff_seconds"]),
                user_agent=str(_need(http, "user_agent", "http")),
            ),
            state_file=Path(paths["state_file"]),
            template_file=Path(paths["template_file"]),
            log_directory=Path(paths["log_directory"]),
            log_level=str(raw["logging"]["level"]).upper(),
            schedule=str(raw["schedule"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc

    if require_email and (not smtp.username or not smtp.password):
        raise ConfigurationError("EMAIL_ADDRESS and EMAIL_PASSWORD environment variables are required")
    if not 1 <= smtp.port <= 65535 or result.http.retry_count < 0:
        raise ConfigurationError("SMTP port must be valid and retry_count cannot be negative")
    if not result.search.results_url.startswith("https://"):
        raise ConfigurationError("search.results_url must use HTTPS")
    return result
