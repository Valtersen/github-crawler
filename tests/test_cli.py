import json
import logging
import pytest
import github_crawler.crawler as crawler_mod

from github_crawler.__main__ import parse_and_normalize_args, main
from tests.conftest import assert_log_contains


def test_invalid_type_exits_with_code_2(capsys):
    """Test that invalid --type argument exits with code 2"""
    argv = ["--type", "Wrong", "--proxies", "host:8080", "--keywords", "python"]
    with pytest.raises(SystemExit) as e:
        parse_and_normalize_args(argv)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "invalid choice" in err
    assert "Repositories" in err


def test_proxy_validation_error_exits_2(capsys):
    """Test that invalid proxy format exits with code 2"""
    argv = ["--type", "Repositories", "--proxies", "bad-proxy", "--keywords", "python"]
    with pytest.raises(SystemExit) as e:
        parse_and_normalize_args(argv)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Invalid proxy format" in err


def test_with_extra_ignored_for_non_repos(capsys):
    """Test that --with-extra is ignored for non-repository search types"""
    argv = [
        "--type",
        "Issues",
        "--proxies",
        "host:8080",
        "--keywords",
        "python",
        "--with-extra",
    ]
    cfg, _ = parse_and_normalize_args(argv)
    err = capsys.readouterr().err
    assert "--with-extra ignored" in err
    assert cfg["with_extra"] is False


def test_output_dir_nonexistent_exits_2(tmp_path, capsys):
    """Test that non-existent output directory exits with code 2"""
    nonexist = tmp_path / "does-not-exist" / "out.json"
    argv = [
        "--type",
        "Repositories",
        "--proxies",
        "host:8080",
        "--keywords",
        "k",
        "--output",
        str(nonexist),
    ]
    with pytest.raises(SystemExit) as e:
        parse_and_normalize_args(argv)
    err = capsys.readouterr().err
    assert e.value.code == 2
    assert "Output directory does not exist" in err


@pytest.mark.asyncio
async def test_main_prints_json_and_writes_file(tmp_path, capsys, monkeypatch):
    """Test successful execution with JSON output and file writing"""

    def fake_init(self, **kwargs):
        pass

    async def fake_run(self):
        return [{"url": "https://github.com/name/repo", "name": "Репозиторій"}]

    monkeypatch.setattr(crawler_mod.Crawler, "__init__", fake_init)
    monkeypatch.setattr(crawler_mod.Crawler, "run", fake_run)

    outfile = tmp_path / "out.json"
    argv = [
        "--type",
        "Repositories",
        "--proxies",
        "host:8080",
        "--keywords",
        "python",
        "httpx",
        "--output",
        str(outfile),
    ]

    await main(argv)

    out = capsys.readouterr()
    data = json.loads(out.out)
    assert isinstance(data, list)
    assert data[0]["url"] == "https://github.com/name/repo"
    assert outfile.exists()
    written = json.loads(outfile.read_text(encoding="utf-8"))
    assert written == data


@pytest.mark.asyncio
async def test_main_error_when_crawler_raises(caplog, monkeypatch):
    """Test error handling when crawler raises an exception"""

    def fake_init(self, **kwargs):
        pass

    async def fake_run(self):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(crawler_mod.Crawler, "__init__", fake_init)
    monkeypatch.setattr(crawler_mod.Crawler, "run", fake_run)

    caplog.set_level(logging.ERROR, logger="github_crawler.__main__")

    argv = ["--type", "Repositories", "--proxies", "host:8080", "--keywords", "python"]

    await main(argv)

    assert assert_log_contains(caplog.records, "Crawler execution failed")


@pytest.mark.asyncio
async def test_main_logs_error_when_results_none(caplog, monkeypatch):
    """Test error logging when crawler returns None"""

    def fake_init(self, **kwargs):
        pass

    async def fake_run(self):
        return None

    monkeypatch.setattr(crawler_mod.Crawler, "__init__", fake_init)
    monkeypatch.setattr(crawler_mod.Crawler, "run", fake_run)

    caplog.set_level(logging.ERROR, logger="github_crawler.__main__")

    argv = ["--type", "Repositories", "--proxies", "host:8080", "--keywords", "py"]

    await main(argv)

    assert assert_log_contains(caplog.records, "Crawler returned no results")
