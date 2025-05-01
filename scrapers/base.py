from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional
import aiohttp
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.last_request_time = 0
        self.min_request_interval = 2  # Minimum seconds between requests

    async def get_page_async(self, url: str) -> str:
        """Fetch a page asynchronously with rate limiting."""
        await self._respect_rate_limit()
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                raise

    def get_page(self, url: str) -> str:
        """Fetch a page synchronously with rate limiting."""
        self._respect_rate_limit()
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')

    async def _respect_rate_limit(self):
        """Ensure we don't make requests too frequently."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    @abstractmethod
    async def scrape(self) -> Any:
        """Main scraping method to be implemented by child classes."""
        pass

    def cleanup(self):
        """Cleanup resources."""
        self.session.close() 