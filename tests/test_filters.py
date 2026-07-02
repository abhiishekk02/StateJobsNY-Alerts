from job_alert.filters import JobMatcher
from job_alert.models import Job


def test_all_required_filters_match(search_config) -> None:
    matcher = JobMatcher(search_config)
    assert matcher.matches(Job("1", "Senior PYTHON Engineer", grade="Grade 18", location="Albany County"))


def test_each_required_filter_is_enforced(search_config) -> None:
    matcher = JobMatcher(search_config)
    assert not matcher.matches(Job("1", "Accountant", grade="18", location="Albany"))
    assert not matcher.matches(Job("2", "Python Developer", grade="23", location="Albany"))
    assert not matcher.matches(Job("3", "Python Developer", grade="18", location="Buffalo"))


def test_short_keyword_uses_word_boundary(search_config) -> None:
    matcher = JobMatcher(search_config)
    assert matcher.matches_title(Job("1", "ITS Specialist"))
    assert not matcher.matches_title(Job("2", "Benefits Coordinator"))

