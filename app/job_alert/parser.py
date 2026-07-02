"""Defensive parsers for StateJobsNY result and detail pages."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .exceptions import ParserError
from .models import Job

DETAIL_LINK = re.compile(r"vacancyDetails(?:View)?\.cfm", re.IGNORECASE)
SPACE = re.compile(r"\s+")


def _clean(value: str) -> str:
    return SPACE.sub(" ", value).strip(" \n\r\t:")


def _job_id(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    for key in ("id", "ID", "vacancyID", "VacancyID"):
        if query.get(key) and query[key][0].strip():
            return query[key][0].strip()
    match = re.search(r"(?:id|vacancyid)[=/](\d+)", url, re.IGNORECASE)
    if match:
        return match.group(1)
    raise ParserError(f"Detail link has no recognizable vacancy ID: {url}")


def parse_search_results(html: str, base_url: str) -> list[Job]:
    """Extract unique vacancy links and any table metadata from a result page."""
    soup = BeautifulSoup(html, "html.parser")
    links = [a for a in soup.find_all("a", href=True) if DETAIL_LINK.search(str(a["href"]))]
    if not links:
        page_text = _clean(soup.get_text(" ", strip=True)).lower()
        if any(message in page_text for message in ("no vacancies", "no records", "no results")):
            return []
        raise ParserError(
            "Search results contained neither vacancy links nor a recognized no-results message; "
            "the StateJobsNY markup may have changed"
        )

    jobs: dict[str, Job] = {}
    for link in links:
        url = urljoin(base_url, str(link["href"]))
        job_id = _job_id(url)
        row = link.find_parent("tr")
        values: dict[str, str] = {}
        if row:
            table = row.find_parent("table")
            headers = [_clean(x.get_text(" ", strip=True)).lower() for x in table.find_all("th")] if table else []
            cells = [_clean(x.get_text(" ", strip=True)) for x in row.find_all(["td", "th"])]
            if len(headers) == len(cells):
                values = dict(zip(headers, cells))
        title = _clean(link.get_text(" ", strip=True))
        jobs[job_id] = Job(
            job_id=job_id,
            title=title,
            agency=_pick(values, "agency"),
            grade=_pick(values, "grade", "salary grade"),
            location=_pick(values, "location", "county"),
            posting_date=_pick(values, "date posted", "posted"),
            deadline=_pick(values, "application deadline", "deadline"),
            url=url,
        )
    return list(jobs.values())


def _pick(values: dict[str, str], *names: str) -> str:
    for name in names:
        for key, value in values.items():
            if name == key or name in key:
                return value or "Not provided"
    return "Not provided"


def _label_values(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) >= 2:
            key = _clean(cells[0].get_text(" ", strip=True)).lower()
            value = _clean(" ".join(c.get_text(" ", strip=True) for c in cells[1:]))
            if key and value:
                values[key] = value
    for term in soup.find_all("dt"):
        description = term.find_next_sibling("dd")
        if description:
            values[_clean(term.get_text(" ", strip=True)).lower()] = _clean(
                description.get_text(" ", strip=True)
            )
    # Current pages also use label/value divs and spans.
    for label in soup.find_all(class_=re.compile(r"label|leftCol", re.IGNORECASE)):
        sibling = label.find_next_sibling()
        if sibling:
            key = _clean(label.get_text(" ", strip=True)).lower()
            value = _clean(sibling.get_text(" ", strip=True))
            if key and value and key != value:
                values.setdefault(key, value)
    return values


def parse_job_detail(html: str, summary: Job) -> Job:
    """Merge a detail page into a search-result job."""
    soup = BeautifulSoup(html, "html.parser")
    values = _label_values(soup)
    if not values:
        raise ParserError(
            f"Vacancy {summary.job_id} has no recognizable labeled fields; markup may have changed"
        )

    def field(default: str, *aliases: str) -> str:
        result = _pick(values, *aliases)
        return default if result == "Not provided" else result

    title = field(summary.title, "title", "vacancy title")
    return Job(
        job_id=summary.job_id,
        title=title,
        agency=field(summary.agency, "agency"),
        grade=field(summary.grade, "salary grade", "grade"),
        salary=field(summary.salary, "salary range", "salary"),
        employment_type=field(summary.employment_type, "employment type", "full/part time"),
        location=field(summary.location, "county", "city", "location", "street address"),
        posting_date=field(summary.posting_date, "date posted", "posting date"),
        deadline=field(summary.deadline, "applications due", "application deadline", "deadline date"),
        url=summary.url,
    )
