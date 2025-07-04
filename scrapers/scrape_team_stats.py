from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re
from database.config import get_db_session
from .tables.overall_results import OverallResultsTableScraper
from .tables.home_away_results import HomeAwayResultsTableScraper
from .tables.squad_standard_for import SquadStandardForScraper
from .tables.squad_standard_against import SquadStandardAgainstScraper
from .tables.squad_keeper_for import SquadKeeperForScraper
from .tables.squad_keeper_against import SquadKeeperAgainstScraper
import logging

logger = logging.getLogger(__name__)

class FBrefScraper(BaseScraper):
    """Scraper for FBref football league teams' statistics."""
    
    def __init__(self, season: str = "2024-25", competition_name: str = "Premier League"):
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
        self.season = season
        self.competition_name = competition_name
        
        # Initialize table scrapers
        self.overall_results_scraper = OverallResultsTableScraper(season, competition_name)
        self.home_away_results_scraper = HomeAwayResultsTableScraper(season, competition_name)
        self.squad_standard_for_scraper = SquadStandardForScraper(season, competition_name)
        self.squad_standard_against_scraper = SquadStandardAgainstScraper(season, competition_name)
        self.squad_keeper_for_scraper = SquadKeeperForScraper(season, competition_name)
        self.squad_keeper_against_scraper = SquadKeeperAgainstScraper(season, competition_name)
    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_tables(self, soup: BeautifulSoup) -> dict:
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
        Scrape all tables from the team stats page and save to database.
        Returns a dictionary with table names as keys and table data as values.
        """
        try:
            html = await self.get_page_async(self.base_url)
            soup = self.parse_html(html)
            
            tables_data = self._extract_tables(soup)
            
            # Get database session
            db = get_db_session()
            try:
                # Save team stats to database using specialized scrapers
                self.overall_results_scraper.save_to_db(tables_data, db)
                self.home_away_results_scraper.save_to_db(tables_data, db)
                self.squad_standard_for_scraper.save_to_db(tables_data, db)
                self.squad_standard_against_scraper.save_to_db(tables_data, db)
                self.squad_keeper_for_scraper.save_to_db(tables_data, db)
                self.squad_keeper_against_scraper.save_to_db(tables_data, db)
            finally:
                db.close()
            
            return tables_data
            
        except Exception as e:
            logger.error(f"Error scraping FBref: {str(e)}")
            raise 