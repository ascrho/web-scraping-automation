"""
Abstract base class for all platform scrapers.
Provides common functionality: browser management, waits, retries, and data export.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for platform-specific scrapers."""

    def __init__(self, config: dict):
        self.config = config
        self.driver: webdriver.Chrome | None = None
        self.wait: WebDriverWait | None = None

    def start_browser(self):
        """Initialize Chrome WebDriver with configured options."""
        options = Options()
        if self.config.get("headless", True):
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, self.config.get("timeout", 30))
        logger.info("Browser started (headless=%s)", self.config.get("headless"))

    def stop_browser(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser stopped")

    def wait_and_click(self, selector: str, by: str = By.CSS_SELECTOR):
        element = self.wait.until(EC.element_to_be_clickable((by, selector)))
        element.click()

    def wait_and_send_keys(self, selector: str, text: str, by: str = By.CSS_SELECTOR):
        element = self.wait.until(EC.presence_of_element_located((by, selector)))
        element.clear()
        element.send_keys(text)

    def wait_for_element(self, selector: str, by: str = By.CSS_SELECTOR):
        return self.wait.until(EC.presence_of_element_located((by, selector)))

    def scrape_table(self, selector: str) -> list[list[str]]:
        """Extract data from an HTML table element."""
        table = self.wait_for_element(selector)
        rows = table.find_elements(By.TAG_NAME, "tr")
        data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if not cells:
                cells = row.find_elements(By.TAG_NAME, "th")
            data.append([cell.text.strip() for cell in cells])
        return data

    def to_dataframe(self, data: list[list[str]], has_header: bool = True) -> pd.DataFrame:
        if has_header and len(data) > 1:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame(data)

    def retry(self, func, max_attempts: int | None = None):
        """Execute a function with retry logic."""
        attempts = max_attempts or self.config.get("retry_attempts", 3)
        for attempt in range(1, attempts + 1):
            try:
                return func()
            except Exception as e:
                logger.warning("Attempt %d/%d failed: %s", attempt, attempts, e)
                if attempt == attempts:
                    raise
                time.sleep(2 ** attempt)

    @abstractmethod
    def login(self):
        """Authenticate with the platform."""

    @abstractmethod
    def extract(self, date_from: str, date_to: str) -> pd.DataFrame:
        """Extract data for the given date range."""

    def run(self, date_from: str, date_to: str, output_path: str | None = None) -> pd.DataFrame:
        """Full extraction pipeline: start browser, login, extract, export, stop."""
        try:
            self.start_browser()
            self.retry(self.login)
            df = self.extract(date_from, date_to)

            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_path, index=False, encoding="utf-8")
                logger.info("Exported %d rows to %s", len(df), output_path)

            return df
        finally:
            self.stop_browser()

    @classmethod
    def from_config_file(cls, config_path: str, platform: str) -> "BaseScraper":
        with open(config_path) as f:
            all_config = json.load(f)
        if platform not in all_config:
            raise ValueError(f"Platform '{platform}' not found in config")
        return cls(all_config[platform])
