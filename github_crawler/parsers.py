from lxml import html
import logging

from github_crawler.utils import get_normalized_url
from .settings import RESULT_XPATH, LANGUAGES_XPATH


def parse_search_results(data: str, logger: logging.Logger | None = None) -> list[dict]:
    """
    Parse the HTML search results page and extract URLs
    """
    logger = logger or logging.getLogger(__name__)
    results = []
    try:
        tree = html.fromstring(data)
        result_elements = tree.xpath(RESULT_XPATH)
        if result_elements:
            for url in result_elements:
                results.append({"url": get_normalized_url(url)})
    except Exception as e:
        logger.error(f"Error parsing search results: {type(e).__name__}: {e}")
    return results


def parse_language_stats(
    data: str, logger: logging.Logger | None = None
) -> dict[str, float]:
    """
    Parse the repository page HTML and extract language stats
    """
    logger = logger or logging.getLogger(__name__)
    results = {}
    try:
        tree = html.fromstring(data)
        language_elements = tree.xpath(LANGUAGES_XPATH)
        if not language_elements:
            return results
        for el in language_elements:
            lang = el.xpath("normalize-space(span[1]/text())")
            pct_str = el.xpath("normalize-space(span[last()]/text())")
            if not lang or not pct_str:
                continue
            try:
                results[lang] = float(
                    pct_str.replace("%", "").replace(",", ".").strip()
                )
            except ValueError:
                logger.warning(
                    f"Could not parse percentage for language '{lang}': '{pct_str}'"
                )
                continue
    except Exception as e:
        logger.error(f"Error parsing language stats: {type(e).__name__}: {e}")
    return results
