"""Domain models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """A normalized NY State vacancy."""

    job_id: str
    title: str
    agency: str = "Not provided"
    grade: str = "Not provided"
    salary: str = "Not provided"
    employment_type: str = "Not provided"
    location: str = "Not provided"
    posting_date: str = "Not provided"
    deadline: str = "Not provided"
    url: str = ""
