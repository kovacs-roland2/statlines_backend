from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class FBrefScraper(BaseScraper):
    """Scraper for FBref Premier League statistics."""
    
    def __init__(self):
        super().__init__(
            base_url="https://fbref.com/en/comps/9/Premier-League-Stats",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
        )
        self.min_request_interval = 3  # FBref is sensitive to frequent requests

    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_tables(self,soup: BeautifulSoup) -> dict:
        """Extract all tables from the parsed HTML."""
        tables_data = {}
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            # Get table name from the preceding h2 or h3 tag
            table_name = table.get('id')
            
            # Extract table data
            rows = []
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                if cells:
                    row = [cell.get_text(strip=True) for cell in cells]
                    rows.append(row)
            
            if rows:
                tables_data[table_name] = rows
        
        return tables_data


    async def scrape(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all tables from the Premier League stats page.
        Returns a dictionary with table names as keys and table data as values.
        """
        try:
            html = await self.get_page_async(self.base_url)
            soup = self.parse_html(html)
            
            tables_data = self._extract_tables(soup)
            
            return tables_data
            
        except Exception as e:
            self.logger.error(f"Error scraping FBref: {str(e)}")
            raise 