import logging

import pytest
import httpx
import respx

from github_crawler.utils import make_request
from tests.conftest import assert_log_contains


@pytest.mark.asyncio
async def test_retry_then_success_on_429(sem):
    url = "https://example.com/retry429"
    with respx.mock() as router:
        route = router.get(url).mock(
            side_effect=[
                httpx.Response(429, text="rate limit"),
                httpx.Response(200, text="ok"),
            ]
        )
        async with httpx.AsyncClient() as client:
            resp = await make_request(url, client, sem, max_retries=2)

    assert route.called
    assert route.call_count == 2
    assert resp is not None and resp.status_code == 200 and resp.text == "ok"


@pytest.mark.asyncio
async def test_non_retry_error_returns_none(caplog, sem):
    caplog.set_level(logging.ERROR)
    url = "https://example.com/notfound"
    with respx.mock() as router:
        route = router.get(url).mock(return_value=httpx.Response(404, text="not found"))
        async with httpx.AsyncClient() as client:
            resp = await make_request(url, client, sem, max_retries=3)

    assert route.called
    assert route.call_count == 1
    assert resp is None
    assert assert_log_contains(caplog.records, "not retrying")


@pytest.mark.asyncio
async def test_timeout_then_success(sem):
    """
    First call raises ReadTimeout (subclass of TimeoutException),
    second call succeeds.
    """
    url = "https://example.com/timeout-once"
    call_count = {"n": 0}

    async with httpx.AsyncClient() as client:

        async def mock_get(url_param):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise httpx.ReadTimeout("-", request=None)
            return httpx.Response(200, text="ok")

        client.get = mock_get

        resp = await make_request(url, client, sem, max_retries=2)

    assert call_count["n"] == 2
    assert resp is not None and resp.status_code == 200 and resp.text == "ok"


@pytest.mark.asyncio
async def test_network_error_exhausts_retries_returns_none(caplog, sem):
    caplog.set_level(logging.WARNING)
    url = "https://example.com/always-connect-error"

    async with httpx.AsyncClient() as client:

        async def mock_get(url_param):
            raise httpx.ConnectError("-", request=None)

        client.get = mock_get

        resp = await make_request(url, client, sem, max_retries=2)

    assert resp is None
    assert assert_log_contains(caplog.records, "Retrying in")


@pytest.mark.asyncio
async def test_unexpected_exception_returns_none(caplog, sem):
    caplog.set_level(logging.ERROR)
    url = "https://example.com/unexpected"

    async with httpx.AsyncClient() as client:

        async def mock_get(url_param):
            raise ValueError("-")

        client.get = mock_get

        resp = await make_request(url, client, sem, max_retries=1)

    assert resp is None
    assert assert_log_contains(caplog.records, "Unexpected error")
