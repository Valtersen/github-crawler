import logging
import pytest

from github_crawler.crawler import Crawler
from tests.conftest import assert_log_contains


@pytest.fixture
def fake_resp():

    class FakeResp:
        def __init__(self, text: str = "", status_code: int = 200):
            self.text = text
            self.status_code = status_code

    return FakeResp


def test_format_search_url_encodes_unicode():
    c = Crawler(
        keywords=["пайтон", "httpx"], search_type="Repositories", proxy="http://p:1"
    )
    url = c.format_search_url()
    assert url.startswith("https://github.com/search?")
    assert "q=%D0%BF%D0%B0%D0%B9%D1%82%D0%BE%D0%BD+httpx" in url
    assert "type=Repositories" in url


def test_owner_from_url_success():
    c = Crawler(keywords=["x"], search_type="Repositories", proxy="http://p:1")
    assert c.owner_from_url("https://github.com/name/repo") == "name"


def test_owner_from_url_fail_logs_error(caplog):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")
    c = Crawler(keywords=["x"], search_type="Repositories", proxy="http://p:1")
    assert c.owner_from_url("https://github.com/justname") is None
    assert assert_log_contains(caplog.records, "Could not extract owner")


@pytest.mark.asyncio
async def test_fetch_and_parse_repo(monkeypatch, load_fixture, fake_resp):
    async def mock_fetch(self, url):
        return fake_resp(text=load_fixture("repo_with_langs.html"))

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch)
    c = Crawler(
        keywords=["x"], search_type="Repositories", proxy="http://p:1", with_extra=True
    )
    repo = {"url": "https://github.com/seleniumbase/repo"}
    await c.fetch_and_parse_repo(repo)
    assert repo["extra"]["owner"] == "seleniumbase"
    assert repo["extra"]["language_stats"]["Python"] == pytest.approx(99.0)


@pytest.mark.asyncio
async def test_fetch_and_parse_repo_missing_url_logs(caplog):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")
    c = Crawler(
        keywords=["x"], search_type="Repositories", proxy="http://p:1", with_extra=True
    )
    repo = {}
    await c.fetch_and_parse_repo(repo)
    assert assert_log_contains(caplog.records, "missing 'url' key")


@pytest.mark.asyncio
async def test_fetch_and_parse_repo_empty_response_logs(monkeypatch, caplog, fake_resp):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")

    async def mock_fetch(self, url, **kw):
        return fake_resp(text="")

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch)
    c = Crawler(
        keywords=["x"], search_type="Repositories", proxy="http://p:1", with_extra=True
    )
    repo = {"url": "https://github.com/name/repo"}
    await c.fetch_and_parse_repo(repo)
    assert assert_log_contains(caplog.records, "Could not get details for repository")


@pytest.mark.asyncio
async def test_fetch_and_parse_repo_exception_logs(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")

    async def mock_fetch(self, url, **kw):
        raise RuntimeError("-")

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch)
    c = Crawler(
        keywords=["x"], search_type="Repositories", proxy="http://p:1", with_extra=True
    )
    repo = {"url": "https://github.com/org/repo"}
    await c.fetch_and_parse_repo(repo)
    assert assert_log_contains(caplog.records, "Error parsing repo")


@pytest.mark.asyncio
async def test_get_extra_info_runs_tasks(monkeypatch):
    c = Crawler(
        keywords=["x"], search_type="Repositories", proxy="http://p:1", with_extra=True
    )

    called = {"n": 0}

    async def mock_fetch_and_parse(self, repo):
        called["n"] += 1
        repo["extra"] = {"owner": "o", "language_stats": {}}

    monkeypatch.setattr(Crawler, "fetch_and_parse_repo", mock_fetch_and_parse)

    repos = [{"url": "https://github.com/a/b"}, {"url": "https://github.com/c/d"}]
    await c.get_extra_info(repos)
    assert called["n"] == 2
    assert all("extra" in r for r in repos)


@pytest.mark.asyncio
async def test_run_success_parses_and_extra(monkeypatch, load_fixture, fake_resp):
    search_html = load_fixture("search_repos_page.html")
    repo_html = load_fixture("repo_with_langs.html")

    calls = {"n": 0}

    async def mock_fetch(self, url, **kw):
        calls["n"] += 1
        if "search?" in url:
            return fake_resp(text=search_html)
        return fake_resp(text=repo_html)

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch)

    c = Crawler(
        keywords=["python"],
        search_type="Repositories",
        proxy="http://p:1",
        with_extra=True,
    )

    data = await c.run()

    assert c.client.closed is True
    assert isinstance(data, list) and len(data) == 2
    assert all("url" in r for r in data)
    assert all("extra" in r for r in data)


@pytest.mark.asyncio
async def test_run_search_fetch_failed_logs_and_returns_none(
    monkeypatch, caplog, fake_resp
):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")

    async def mock_fetch_fail(self, url, **kw):
        return fake_resp(text="")

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch_fail)

    c = Crawler(keywords=["x"], search_type="Repositories", proxy="http://p:1")
    res = await c.run()

    assert res is None
    assert c.client.closed is True
    assert assert_log_contains(caplog.records, "Could not get search results")


@pytest.mark.asyncio
async def test_run_catches_exception_and_closes_client(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger="github_crawler.crawler")

    async def mock_fetch_fail(self, url, **kw):
        raise RuntimeError("-")

    monkeypatch.setattr(Crawler, "fetch_url", mock_fetch_fail)

    c = Crawler(keywords=["x"], search_type="Repositories", proxy="http://p:1")
    res = await c.run()

    assert res is None
    assert c.client.closed is True
    assert assert_log_contains(caplog.records, "Crawler run failed")
