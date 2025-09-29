import asyncio
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    def _load(name: str) -> str:
        path = FIXTURES_DIR / name
        return path.read_text(encoding="utf-8")

    return _load


@pytest.fixture
def sem():
    return asyncio.Semaphore(10)


class FakeClient:
    def __init__(self):
        self.closed = False

    async def aclose(self):
        self.closed = True


@pytest.fixture(autouse=True)
def patch_get_request_client(monkeypatch):
    monkeypatch.setattr(
        "github_crawler.crawler.get_request_client",
        lambda proxy: FakeClient(),
    )


def assert_log_contains(caplog_records, message_fragment: str) -> bool:
    """Helper function to check if any log record contains the message fragment"""
    return any(message_fragment in record.message for record in caplog_records)
