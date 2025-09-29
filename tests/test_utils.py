import pytest

# Adjust imports to your structure
from github_crawler.utils import normalize_url, normalize_proxy


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("https://github.com/org/repo", "https://github.com/org/repo"),
        ("/org/repo", "https://github.com/org/repo"),
        ("/org/repo#readme", "https://github.com/org/repo"),
    ],
)
def test_normalize_url(inp, expected):
    assert normalize_url(inp) == expected


@pytest.mark.parametrize(
    "inp,expected",
    [
        ("host:8080", "http://host:8080"),
        ("http://host:8080", "http://host:8080"),
        ("http://user:pass@host:8080", "http://user:pass@host:8080"),
    ],
)
def test_normalize_proxy_ok(inp, expected):
    assert normalize_proxy(inp) == expected


@pytest.mark.parametrize(
    "bad",
    ["host", "http://host", "http://host:notaport", "://host:8080", "http:///8080"],
)
def test_normalize_proxy_bad(bad):
    with pytest.raises(ValueError):
        normalize_proxy(bad)
