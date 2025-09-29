import logging

import pytest

from github_crawler.parsers import parse_search_results, parse_language_stats
from tests.conftest import assert_log_contains


def test_parse_search_results_basic(load_fixture):
    html = load_fixture("search_repos_page.html")
    urls = parse_search_results(html)
    assert urls == [
        {"url": "https://github.com/atuldjadhav/DropBox-Cloud-Storage"},
        {"url": "https://github.com/michealbalogun/Horizon-dashboard"},
    ]


def test_parse_search_results_zero(load_fixture):
    html = load_fixture("search_zero_results.html")
    urls = parse_search_results(html)
    assert urls == []


def test_parse_language_stats(load_fixture):
    expected = {
        "Python": 99.0,
        "Shell": 0.4,
        "HTML": 0.3,
        "Gherkin": 0.2,
        "Dockerfile": 0.1,
        "Batchfile": 0.0,
    }

    html = load_fixture("repo_with_langs.html")
    langs = parse_language_stats(html)
    for lang, pct in expected.items():
        assert lang in langs
        assert langs[lang] == pytest.approx(pct)


def test_parse_language_stats_empty(load_fixture):
    html = load_fixture("repo_no_langs.html")
    assert parse_language_stats(html) == {}


def test_parse_search_results_logs_error_on_bad_html(caplog):
    caplog.set_level(logging.ERROR)
    out = parse_search_results("")
    assert out == []
    assert assert_log_contains(caplog.records, "Error parsing search results")


def test_parse_language_stats_logs_error_on_bad_html(caplog):
    caplog.set_level(logging.ERROR)
    langs = parse_language_stats("")  # Use empty string instead of None
    assert langs == {}
    assert assert_log_contains(caplog.records, "Error parsing language stats")
