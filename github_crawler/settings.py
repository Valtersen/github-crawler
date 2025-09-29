"""
Settings and constants for GitHub crawler.
"""

# Base URL for all GitHub requests
BASE_URL: str = "https://github.com/"

# Supported search types for the crawler
SEARCH_TYPES: list[str] = ["Repositories", "Issues", "Wikis"]

# User agent string for requests
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# Default headers for requests
HEADERS: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US;q=0.9,en;q=0.8",
    "dnt": "1",
    "upgrade-insecure-requests": "1",
    "referer": BASE_URL,
}

# Maximum number of concurrent requests
MAX_CONCURRENT_REQUESTS: int = 5

# Timeout for requests (seconds)
TIMEOUT: int = 15

# Whether to follow redirects in requests
FOLLOW_REDIRECTS: bool = True

# HTTP status codes that should trigger a retry
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Maximum number of retry attempts
MAX_RETRIES: int = 5

# Exponential backoff base and cap for retries (seconds)
BACKOFF_BASE: float = 0.5
BACKOFF_CAP: float = 20.0


# XPath for extracting search result URLs
RESULT_XPATH: str = "//div[contains(@class, 'search-title')]/a/@href"

# XPath for extracting language statistics from repository page
LANGUAGES_XPATH: str = (
    "//div[@class='Layout-sidebar']//h2[contains(text(), 'Languages')]/..//a"
)
