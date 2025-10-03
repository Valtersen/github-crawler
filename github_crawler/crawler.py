import asyncio
import logging
from asyncio import Semaphore
from urllib.parse import urlparse

import httpx

from .parsers import parse_search_results, parse_language_stats
from .settings import MAX_CONCURRENT_REQUESTS
from .utils import make_request, get_normalized_url, get_request_client


class Crawler:
    def __init__(
        self,
        keywords: list[str],
        search_type: str,
        proxy: str,
        with_extra: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)
        self.client = get_request_client(proxy)
        self.keywords = keywords
        self.search_type = search_type
        self.proxy = proxy
        self.with_extra = with_extra

    async def fetch_url(self, url: str, params: dict | None = None, **kwargs) -> httpx.Response | None:
        """
        Fetch a URL asynchronously using the configured client and semaphore
        """
        return await make_request(
            url, self.client, self.semaphore, params=params, logger=self.logger, **kwargs
        )

    def get_search_url_with_params(self) -> tuple[str, dict]:
        """
        Get the GitHub search URL and query parameters.

        Returns:
            Tuple of (base_url, params_dict)
        """
        query = " ".join(self.keywords)
        params = {"q": query, "type": self.search_type}
        return get_normalized_url("search"), params

    def owner_from_url(self, url: str) -> str | None:
        """
        Extract the repository owner from a GitHub URL
        """
        parts = urlparse(url).path.strip("/").split("/")
        if len(parts) >= 2:
            return parts[-2]

        self.logger.error(f"Could not extract owner from repository url: {url}")
        return None

    async def fetch_and_parse_repo(self, repo: dict) -> None:
        """
        Fetch repository page and parse extra info (owner, language stats).
        """
        repo_url = repo.get("url")
        if not repo_url:
            self.logger.error("Repository dict missing 'url' key.")
            return None
        try:
            repo_data = await self.fetch_url(repo_url)
            if not repo_data or not repo_data.text:
                self.logger.error(f"Could not get details for repository {repo_url}")
                return None
            language_stats = parse_language_stats(repo_data.text)
            owner = self.owner_from_url(repo_url)
            repo["extra"] = {"language_stats": language_stats, "owner": owner}
        except Exception as e:
            self.logger.error(f"Error parsing repo {repo_url}: {type(e).__name__}: {e}")

    async def get_extra_info(self, repos: list[dict]) -> None:
        """
        Fetch and parse extra info for all repositories in parallel.
        """
        if not repos:
            return

        tasks = [self.fetch_and_parse_repo(repo) for repo in repos]
        await asyncio.gather(*tasks)

    async def run(self) -> list[dict] | None:
        """
        Run the crawler: search, parse results, and optionally fetch extra info.
        """
        try:
            search_url, search_params = self.get_search_url_with_params()
            search_data = await self.fetch_url(search_url, params=search_params)
            if not search_data or not search_data.text:
                self.logger.error(
                    f"Could not get search results for {self.keywords} and type {self.search_type} "
                    f"with {self.proxy} proxy"
                )
                return None
            parsed_data = parse_search_results(search_data.text)
            if parsed_data and self.search_type == "Repositories" and self.with_extra:
                await self.get_extra_info(parsed_data)

            return parsed_data
        except Exception as e:
            self.logger.error(f"Crawler run failed: {type(e).__name__}: {e}")
            return None
        finally:
            await self.client.aclose()
