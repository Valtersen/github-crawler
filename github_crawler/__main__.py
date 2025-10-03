import json
import os
import random
import sys
import argparse
import asyncio
import logging

from github_crawler.crawler import Crawler
from github_crawler.settings import SEARCH_TYPES
from github_crawler.utils import normalize_proxy


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with proper formatting."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_and_normalize_args(argv: list[str] | None = None) -> tuple[dict, str | None]:
    """
    Parse and validate CLI arguments.

    Args:
        argv: command line arguments list

    Returns: tuple of (config dict, output filename)
    """
    p = argparse.ArgumentParser(description="GitHub search crawler")
    p.add_argument(
        "--type", required=True, choices=SEARCH_TYPES, help="Type of search to perform"
    )
    p.add_argument(
        "--proxies",
        required=True,
        nargs="+",
        help="List of proxies in format host:port",
    )
    p.add_argument("--keywords", required=True, nargs="+", help="Search keywords")
    p.add_argument("--output", help="Optional output path for JSON results")
    p.add_argument(
        "--with-extra",
        action="store_true",
        help="Repositories type only: include owner and language stats",
    )

    a = p.parse_args(argv)

    try:
        normalized_proxies = [normalize_proxy(pr.strip()) for pr in a.proxies]
    except ValueError as e:
        p.error(f"Invalid proxy format: {e}")

    if a.output:
        outdir = os.path.dirname(a.output) or "."
        if not os.path.exists(outdir):
            p.error(f"Output directory does not exist: {outdir}")

    if a.with_extra and a.type != "Repositories":
        p.error("--with-extra can only be used with Repositories type")

    return {
        "keywords": a.keywords,
        "search_type": a.type,
        "proxies": normalized_proxies,
        "with_extra": a.with_extra,
    }, a.output


async def main(argv=None):
    setup_logging()
    logger = logging.getLogger(__name__)
    cfg, output_filename = parse_and_normalize_args(argv)

    # Select proxy randomly
    proxy = random.choice(cfg.pop("proxies"))
    cfg["proxy"] = proxy

    logger.info(f"Using proxy: {proxy}")

    try:
        results = await Crawler(**cfg, logger=logger).run()
    except Exception as e:
        logger.error(f"Crawler execution failed: {type(e).__name__}: {e}")
        return

    if results is None:
        logger.error("Crawler returned no results")
        return

    results_formatted = json.dumps(results, indent=2)
    logger.info(f"Found {len(results)} results")
    sys.stdout.write(results_formatted)

    if output_filename:
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(results_formatted)
            logger.info(f"Results written to {output_filename}")
        except Exception as e:
            logger.error(
                f"Failed to write output file {output_filename}: {type(e).__name__}: {e}"
            )
            return


if __name__ == "__main__":
    asyncio.run(main())
