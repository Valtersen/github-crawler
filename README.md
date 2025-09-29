# GitHub Crawler

A Python-based GitHub search crawler that extracts search results from GitHub's web interface using raw HTML parsing. The crawler supports searching for Repositories, Issues, and Wikis with proxy support and optional extended repository information.

## Requirements

- Python 3.10+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Valtersen/github-crawler
cd github-crawler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. For development (includes testing tools):
```bash
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage

```bash
python -m github_crawler --type Repositories --keywords openstack nova css --proxies 194.126.37.94:8080 13.78.125.167:8080
```

### Command Line Arguments

- `--type`: Type of search to perform (required)
  - Options: `Repositories`, `Issues`, `Wikis`
- `--keywords`: Search keywords (required, space-separated)
- `--proxies`: List of proxies in format `host:port` (required, space-separated)
- `--output`: Optional output file path for JSON results
- `--with-extra`: Include repository owner and language stats (Repositories only)

### Examples

#### Basic Repository Search
```bash
python -m github_crawler \
  --type Repositories \
  --keywords openstack nova css \
  --proxies 194.126.37.94:8080 13.78.125.167:8080
```

#### Repository Search with Extended Information
```bash
python -m github_crawler \
  --type Repositories \
  --keywords python machine learning \
  --proxies 194.126.37.94:8080 \
  --with-extra \
  --output results.json
```

#### Issues Search
```bash
python -m github_crawler \
  --type Issues \
  --keywords openstack nova css \
  --proxies 194.126.37.94:8080
```

#### Wikis Search
```bash
python -m github_crawler \
  --type Wikis \
  --keywords openstack nova css \
  --proxies 194.126.37.94:8080
```

#### Unicode Keywords Support
```bash
python -m github_crawler \
  --type Repositories \
  --keywords 数据库 机器学习 \
  --proxies 194.126.37.94:8080
```

## Output Format

The crawler outputs JSON data to stdout and optionally to a file specified with `--output`.

### Basic Output (all types)
```json
[
  {
    "url": "https://github.com/owner/repository-name",
    "title": "Repository Title"
  }
]
```

### Extended Repository Output (with --with-extra)
```json
[
  {
    "url": "https://github.com/owner/repository-name",
    "title": "Repository Title",
    "extra": {
      "owner": "owner",
      "language_stats": {
        "Python": "85.2%",
        "JavaScript": "10.1%",
        "CSS": "4.7%"
      }
    }
  }
]
```

## Testing

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage Report
```bash
pytest --cov=github_crawler
```


### Test Fixtures

The tests include HTML fixtures in `tests/fixtures/` directory:
- `search_repos_page.html`: Sample GitHub search results page
- `search_zero_results.html`: Empty search results page
- `repo_with_langs.html`: Repository page with language statistics
- `repo_no_langs.html`: Repository page without language data


## Configuration

### Performance Tuning

You can adjust performance settings in `settings.py`:

- `MAX_CONCURRENT_REQUESTS`: Maximum concurrent HTTP requests (default: 5)
- `TIMEOUT`: Request timeout in seconds (default: 15)


### Runtime Dependencies
- `httpx`: Async HTTP client for web requests
- `lxml`: Fast XML/HTML parser

### Development Dependencies
- `pytest`: Testing framework
- `pytest-asyncio`: Async testing support
- `pytest-cov`: Coverage reporting
- `respx`: HTTP mocking for tests
