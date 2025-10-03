import asyncio
import logging
import random
from asyncio import Semaphore
from urllib.parse import urlparse, urljoin, urldefrag

import httpx

from .settings import (
    BASE_URL,
    TIMEOUT,
    HEADERS,
    FOLLOW_REDIRECTS,
    RETRY_STATUS_CODES,
    BACKOFF_CAP,
    BACKOFF_BASE,
    MAX_RETRIES,
)


def get_request_client(proxy: str) -> httpx.AsyncClient:
    """
    Create and return an AsyncClient configured with proxy and default settings
    """
    return httpx.AsyncClient(
        timeout=TIMEOUT,
        proxy=proxy,
        headers=HEADERS,
        follow_redirects=FOLLOW_REDIRECTS,
    )


def get_normalized_url(url: str) -> str:
    """
    Normalize a relative or absolute URL to a full GitHub URL
    """
    absu, _ = urldefrag(urljoin(BASE_URL, url))
    return absu


def normalize_proxy(p: str) -> str:
    """
    Normalize a proxy string to a full URL. Raises ValueError if invalid
    """
    if "://" not in p:
        p = "http://" + p
    u = urlparse(p)
    if not u.hostname or not u.port:
        raise ValueError(f"Invalid proxy: {p}")
    return p


def get_expo_backoff(
    attempt: int, base: float = BACKOFF_BASE, cap: float = BACKOFF_CAP
) -> float:
    """Calculate exponential backoff delay with jitter"""
    delay = min(cap, base * (2**attempt)) * (0.5 + random.random())
    return round(delay, 2)


async def make_request(
    url: str,
    client: httpx.AsyncClient,
    sem: Semaphore,
    params: dict | None = None,
    max_retries: int = MAX_RETRIES,
    logger: logging.Logger | None = None,
) -> httpx.Response | None:
    """
    Make an async GET request with semaphore and retries.

    Args:
        url: The URL to request
        client: The httpx.AsyncClient
        sem: Semaphore
        params: Optional query parameters dict
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance, creates default if None

    Returns:
        httpx.Response object if successful, None if failed
    """
    if not logger:
        logger = logging.getLogger(__name__)

    for attempt in range(max_retries + 1):
        try:
            async with sem:
                response = await client.get(url, params=params)

            # Check for HTTP error status codes that should be retried
            if response.status_code in RETRY_STATUS_CODES:
                if attempt < max_retries:
                    delay = get_expo_backoff(attempt)
                    logger.warning(
                        f"HTTP {response.status_code} for {url}. Retrying in {delay}s"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"HTTP {response.status_code} for {url} after {max_retries + 1} attempts"
                    )
                    return None

            # Check for non-retry HTTP errors
            if not response.is_success:
                logger.error(f"HTTP {response.status_code} for {url} - not retrying")
                return None

            return response

        except (httpx.TimeoutException, httpx.NetworkError) as e:
            if attempt < max_retries:
                delay = get_expo_backoff(attempt)
                logger.warning(
                    f"Request failed for {url}: {type(e).__name__} {e}. Retrying in {delay}s"
                )
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(
                    f"Failed to fetch {url} after {max_retries + 1} attempts: {type(e).__name__} {e}"
                )
                return None

        except Exception as e:
            logger.error(f"Unexpected error for {url}: {type(e).__name__} {e}")
            return None

    return None
