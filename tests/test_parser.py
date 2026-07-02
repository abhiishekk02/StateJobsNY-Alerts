import pytest

from job_alert.exceptions import ParserError
from job_alert.models import Job
from job_alert.parser import parse_job_detail, parse_search_results


RESULTS = """
<table><tr><th>Title</th><th>Agency</th><th>Grade</th><th>County</th></tr>
<tr><td><a href="vacancyDetailsView.cfm?id=12345">Python Developer</a></td>
<td>Office of Technology</td><td>18</td><td>Albany</td></tr></table>
"""

DETAIL = """
<dl><dt>Title</dt><dd>Python Developer</dd><dt>Agency</dt><dd>Office of Technology</dd>
<dt>Salary Grade</dt><dd>18</dd><dt>Salary Range</dt><dd>$65,000 - $82,000</dd>
<dt>Employment Type</dt><dd>Full-Time</dd><dt>City</dt><dd>Albany</dd>
<dt>Date Posted</dt><dd>07/02/2026</dd><dt>Application Deadline</dt><dd>07/17/2026</dd></dl>
"""

CURRENT_DETAIL = """
<div class="columnReport">
<p class="row"><span class="leftCol"><a class="help"></a>Date Posted</span><span class="rightCol">07/02/26</span></p>
<p class="row"><span class="leftCol">Applications Due</span><span class="rightCol">07/19/26</span></p>
<p class="row"><span class="leftCol">Agency</span><span class="rightCol">Teachers' Retirement System</span></p>
<p class="row"><span class="leftCol">Title</span><span class="rightCol">Information Technology Specialist 2</span></p>
<p class="row"><span class="leftCol">Salary Grade</span><span class="rightCol">18</span></p>
<p class="row"><span class="leftCol">Salary Range</span><span class="rightCol">From $78669 to $115477 Annually</span></p>
<p class="row"><span class="leftCol">Employment Type</span><span class="rightCol">Full-Time</span></p>
<p class="row"><span class="leftCol">County</span><span class="rightCol">Albany</span></p>
<p class="row"><span class="leftCol">Street Address</span><span class="rightCol">10 Corporate Woods Drive</span></p>
</div>
"""


def test_parse_result_and_detail() -> None:
    jobs = parse_search_results(RESULTS, "https://statejobs.ny.gov/public/vacancyTable.cfm")
    assert len(jobs) == 1
    assert jobs[0].job_id == "12345"
    assert jobs[0].agency == "Office of Technology"
    detailed = parse_job_detail(DETAIL, jobs[0])
    assert detailed.salary == "$65,000 - $82,000"
    assert detailed.location == "Albany"
    assert detailed.deadline == "07/17/2026"


def test_no_results_is_valid() -> None:
    assert parse_search_results("<p>No vacancies found.</p>", "https://example.test") == []


def test_current_statejobs_detail_markup() -> None:
    summary = Job("219018", "ITS 2", url="https://example.test/vacancyDetailsView.cfm?id=219018")
    detailed = parse_job_detail(CURRENT_DETAIL, summary)
    assert detailed.location == "Albany"
    assert detailed.deadline == "07/19/26"
    assert detailed.salary == "From $78669 to $115477 Annually"


def test_unknown_markup_fails_meaningfully() -> None:
    with pytest.raises(ParserError, match="markup may have changed"):
        parse_search_results("<html><p>Unexpected page</p></html>", "https://example.test")


def test_detail_without_fields_fails() -> None:
    with pytest.raises(ParserError, match="no recognizable"):
        parse_job_detail("<h1>Broken</h1>", Job("7", "Python", url="https://example.test/7"))
