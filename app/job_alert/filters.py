"""Configurable, all-required job matching."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import SearchConfig
from .models import Job


def _contains(text: str, value: str) -> bool:
    """Match phrases case-insensitively; short terms require word boundaries."""
    normalized = " ".join(text.casefold().split())
    needle = " ".join(value.casefold().split())
    if len(needle) <= 4 and needle.isalnum():
        return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", normalized) is not None
    return needle in normalized


def _grade_matches(actual: str, expected: str) -> bool:
    expected_number = expected.casefold().removeprefix("grade").strip().lstrip("0") or "0"
    numbers = re.findall(r"\d+", actual)
    return any((number.lstrip("0") or "0") == expected_number for number in numbers)


@dataclass(frozen=True)
class JobMatcher:
    """Require one configured title keyword, location, and grade."""

    config: SearchConfig

    def matches_title(self, job: Job) -> bool:
        return any(_contains(job.title, keyword) for keyword in self.config.keywords)

    def matches(self, job: Job) -> bool:
        return (
            self.matches_title(job)
            and any(_contains(job.location, location) for location in self.config.locations)
            and any(_grade_matches(job.grade, grade) for grade in self.config.grades)
        )
