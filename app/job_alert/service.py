"""Application orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from .client import StateJobsClient
from .config import AppConfig
from .filters import JobMatcher
from .models import Job
from .parser import parse_job_detail, parse_search_results
from .storage import SeenJobStore


class Notifier(Protocol):
    def send(self, job: Job) -> None: ...


@dataclass(frozen=True)
class RunStats:
    found: int
    matched: int
    sent: int
    skipped_seen: int


class JobAlertService:
    """Search, enrich, filter, notify, and persist in safe order."""

    def __init__(
        self,
        config: AppConfig,
        client: StateJobsClient,
        store: SeenJobStore,
        notifier: Notifier,
    ) -> None:
        self.config = config
        self.client = client
        self.store = store
        self.notifier = notifier
        self.matcher = JobMatcher(config.search)
        self.logger = logging.getLogger(__name__)

    def run(self) -> RunStats:
        broad_search = bool(getattr(self.notifier, "broad_search", False))
        params = {"searchResults": "Yes"}
        if not broad_search:
            params["gradeCompareType"] = "EQ"
            params["grade"] = self.config.search.grades[0].zfill(2)
            for region in self.config.search.regions:
                params[f"region{region}"] = region
        html = self.client.get(self.config.search.results_url, params)
        summaries = parse_search_results(html, self.config.search.results_url)
        matched = sent = skipped = 0
        self.logger.info("Search returned %d vacancy records", len(summaries))
        for summary in summaries:
            if self.store.contains(summary.job_id):
                skipped += 1
                continue
            if not self.matcher.matches_title(summary):
                continue
            detail = parse_job_detail(self.client.get(summary.url), summary)
            if broad_search:
                # Subscriber-specific location and grade comparisons happen in the API.
                is_match = self.matcher.matches_title(detail)
            else:
                is_match = self.matcher.matches(detail)
            if not is_match:
                continue
            matched += 1
            self.notifier.send(detail)
            # Persist only after the delivery service accepts it; failures are retried.
            self.store.mark_sent(detail.job_id, detail.title)
            sent += 1
            self.logger.info("Alert sent for vacancy %s: %s", detail.job_id, detail.title)
        return RunStats(len(summaries), matched, sent, skipped)
