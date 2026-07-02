"""HTTP client with session reuse and bounded retries."""

from __future__ import annotations

import logging
import time
from typing import Mapping

import requests

from .config import HttpConfig
from .exceptions import FetchError


class StateJobsClient:
    """Fetch StateJobsNY pages using one reusable session."""

    def __init__(self, config: HttpConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent, "Accept": "text/html"})
        self.logger = logging.getLogger(__name__)

    def get(self, url: str, params: Mapping[str, str] | None = None) -> str:
        last_error: Exception | None = None
        attempts = self.config.retry_count + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.config.timeout_seconds)
                response.raise_for_status()
                if "html" not in response.headers.get("Content-Type", "text/html").lower():
                    raise FetchError(f"Unexpected content type from {response.url}")
                return response.text
            except (requests.RequestException, FetchError) as exc:
                last_error = exc
                if attempt < attempts:
                    delay = self.config.backoff_seconds * (2 ** (attempt - 1))
                    self.logger.warning(
                        "Request attempt %d/%d failed: %s; retrying in %.1fs",
                        attempt, attempts, exc, delay,
                    )
                    time.sleep(delay)
        raise FetchError(f"Failed to fetch {url} after {attempts} attempts: {last_error}")

