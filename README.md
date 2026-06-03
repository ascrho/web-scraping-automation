# Web Scraping Automation Framework

> Configurable Selenium-based automation framework for multi-platform data extraction with external configuration and retry logic.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium&logoColor=white)](https://selenium.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## Overview

Production-tested framework for automating data extraction from web platforms that don't provide APIs. Designed for enterprise use with external configuration, structured logging, and error recovery.

## Features

- **External configuration** — All credentials and parameters in `config.json` (never hardcoded)
- **Multi-platform support** — Modular design for adding new platform scrapers
- **Retry logic** — Automatic retries with configurable backoff for transient failures
- **WebDriverWait** — Explicit waits instead of `time.sleep()` for reliability
- **Stale element handling** — Automatic recovery from `StaleElementReferenceException`
- **Structured output** — JSON and CSV exports with standardized schemas
- **Headless mode** — Optional headless browser execution for CI/CD

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  config.json     │────▶│  Scraper Engine  │────▶│  Output Files    │
│  (credentials,   │     │  (Selenium +     │     │  (JSON / CSV)    │
│   parameters)    │     │   BeautifulSoup) │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

## Quick Start

### 1. Configure

```bash
cp config/config.json.example config/config.json
# Edit with your platform credentials
```

```json
{
  "platform_name": {
    "url": "https://platform.example.com",
    "username": "your-user",
    "password": "your-password",
    "output_dir": "./output",
    "headless": true,
    "timeout": 30,
    "retry_attempts": 3
  }
}
```

### 2. Run

```bash
# Extract data from a specific platform
python scrapers/platform_scraper.py --config config/config.json --platform platform_name

# Extract with date range
python scrapers/platform_scraper.py --config config/config.json --from 2024-01-01 --to 2024-12-31

# Dry run (login only, no extraction)
python scrapers/platform_scraper.py --config config/config.json --dry-run
```

## Project Structure

```
web-scraping-automation/
├── scrapers/
│   ├── base_scraper.py          # Abstract base class
│   ├── ticketing_scraper.py     # Ticketing platform scraper
│   ├── telephony_scraper.py     # Call center data scraper
│   └── regulatory_scraper.py    # Regulatory portal scraper
├── utils/
│   ├── browser.py               # WebDriver factory
│   ├── retry.py                 # Retry decorator with backoff
│   └── logger.py                # Structured logging
├── config/
│   └── config.json.example      # Configuration template
├── output/                      # Generated data files
├── requirements.txt
└── README.md
```

## Base Scraper Pattern

All scrapers extend a common base class:

```python
from scrapers.base_scraper import BaseScraper

class TicketingScraper(BaseScraper):
    def login(self):
        self.driver.get(self.config["url"])
        self.wait_and_send_keys("#username", self.config["username"])
        self.wait_and_send_keys("#password", self.config["password"])
        self.wait_and_click("#login-btn")
        self.wait_for_element("#dashboard")

    def extract(self, date_from, date_to):
        self.navigate_to_reports()
        self.set_date_range(date_from, date_to)
        data = self.scrape_table("#results-table")
        return self.to_dataframe(data)

    def export(self, df, output_path):
        df.to_csv(output_path, index=False, encoding="utf-8")
```

## Retry Logic

```python
from utils.retry import retry_on_failure

@retry_on_failure(max_attempts=3, backoff_factor=2)
def scrape_with_retry(scraper, params):
    return scraper.extract(**params)
```

## Technologies

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Browser Automation | Selenium WebDriver 4.x |
| HTML Parsing | BeautifulSoup 4 |
| Data Processing | pandas |
| Configuration | JSON |
| Logging | Python logging |

## Requirements

```
selenium>=4.15
beautifulsoup4>=4.12
pandas>=2.0
webdriver-manager>=4.0
requests>=2.31
```

## License

MIT License

## Author

**Marcos Quintero** — Data Engineer  
[GitHub](https://github.com/MarcosQuintero) | [LinkedIn](https://www.linkedin.com/in/marcosquinterero-dataengineer/)
