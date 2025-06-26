from typing import Dict, List, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re
from database.config import get_db_session
from database.models import TeamOverallTableResults, Team, Competition, TeamHomeAwayTableResults
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class FBrefScraper(BaseScraper):
    """Scraper for FBref Premier League statistics."""
    
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

    def _get_or_create_competition(self, db: Session) -> Competition:
        """Get or create competition record."""
        competition = db.execute(
            select(Competition).where(Competition.name == self.competition_name)
        ).scalar_one_or_none()
        
        if not competition:
            competition = Competition(
                name=self.competition_name,
            )
            db.add(competition)
            db.commit()
            db.refresh(competition)
            logger.info(f"Created new competition: {self.competition_name}")
        
        return competition

    def _get_or_create_team(self, db: Session, team_name: str, competition_id: int) -> Team:
        """Get or create team record."""
        team = db.execute(
            select(Team).where(Team.name == team_name)
        ).scalar_one_or_none()
        
        if not team:
            team = Team(
                name=team_name,
                competition_id=competition_id
            )
            db.add(team)
            db.commit()
            db.refresh(team)
            logger.info(f"Created new team: {team_name}")
        
        return team

    def _parse_numeric_value(self, value: str) -> float:
        """Parse numeric values, handling different formats."""
        if not value or value == '':
            return None
        
        # Remove any '+' signs and convert to float
        value = value.replace('+', '').replace(',', '')
        try:
            return float(value)
        except ValueError:
            return None

    def _save_team_overall_table_results_to_db(self, tables_data: dict) -> None:
        """Save team stats data to the database."""
        db = get_db_session()
        try:
            # Get or create competition
            competition = self._get_or_create_competition(db)
            
            # Find the overall results table
            overall_table = None
            for table_name, table_data in tables_data.items():
                if 'overall' in table_name.lower() and 'results' in table_name.lower():
                    overall_table = table_data
                    break
            
            if not overall_table:
                logger.warning("Could not find overall results table")
                return
            
            # Skip header row
            data_rows = overall_table[1:]
            
            for row in data_rows:
                if len(row) < 10:  # Ensure we have enough columns
                    continue
                
                squad_name = row[1]  # Squad column
                
                # Get or create team
                team = self._get_or_create_team(db, squad_name, competition.id)
                
                # Check if stats for this team and season already exist
                existing_stats = db.execute(
                    select(TeamOverallTableResults).where(
                        TeamOverallTableResults.team_id == team.id,
                        TeamOverallTableResults.season == self.season,
                        TeamOverallTableResults.competition_id == competition.id
                    )
                ).scalar_one_or_none()
                
                if existing_stats:
                    # Update existing record
                    stats_record = existing_stats
                else:
                    # Create new record
                    stats_record = TeamOverallTableResults(
                        team_id=team.id,
                        competition_id=competition.id,
                        season=self.season
                    )
                
                # Map the data to the model fields
                stats_record.rk = int(row[0]) if row[0].isdigit() else None
                stats_record.squad = squad_name
                stats_record.mp = int(row[2]) if row[2].isdigit() else None
                stats_record.w = int(row[3]) if row[3].isdigit() else None
                stats_record.d = int(row[4]) if row[4].isdigit() else None
                stats_record.l = int(row[5]) if row[5].isdigit() else None
                stats_record.gf = int(row[6]) if row[6].isdigit() else None
                stats_record.ga = int(row[7]) if row[7].isdigit() else None
                stats_record.gd = int(row[8].replace('+', '')) if row[8] and row[8] != '' else None
                stats_record.pts = int(row[9]) if row[9].isdigit() else None
                stats_record.pts_per_mp = self._parse_numeric_value(row[10])
                stats_record.xg = self._parse_numeric_value(row[11])
                stats_record.xga = self._parse_numeric_value(row[12])
                stats_record.xgd = self._parse_numeric_value(row[13])
                stats_record.xgd_per_90 = self._parse_numeric_value(row[14])
                
                if not existing_stats:
                    db.add(stats_record)
            
            db.commit()
            logger.info(f"Successfully saved team stats for season {self.season}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving team stats to database: {str(e)}")
            raise
        finally:
            db.close()

    def _save_team_home_away_table_results_to_db(self, tables_data: dict) -> None:
        """Save home/away split team stats to the database."""
        db = get_db_session()
        try:
            competition = self._get_or_create_competition(db)
            # Find the home/away table (look for 'home' and 'away' in the table name)
            home_away_table = None
            for table_name, table_data in tables_data.items():
                if 'home' in table_name.lower() and 'away' in table_name.lower():
                    home_away_table = table_data
                    break
            if not home_away_table or len(home_away_table) < 3:
                logger.warning("Could not find home/away table or table is too short")
                return
            # The first two rows are headers: first is Home/Away, second is stat names
            header_stats = home_away_table[1]
            data_rows = home_away_table[2:]
            # Build index lists for home and away columns
            home_indices = [i for i in range(2, 15)]
            away_indices = [i for i in range(15, 28)]
            # For each row, parse home and away stats
            for row_idx, row in enumerate(data_rows):
                squad_name = row[1]  # Team name is usually the second column
                team = self._get_or_create_team(db, squad_name, competition.id)
                # Check if record exists
                existing = db.execute(
                    select(TeamHomeAwayTableResults).where(
                        TeamHomeAwayTableResults.team_id == team.id,
                        TeamHomeAwayTableResults.season == self.season,
                        TeamHomeAwayTableResults.competition_id == competition.id
                    )
                ).scalar_one_or_none()
                if existing:
                    record = existing
                else:
                    record = TeamHomeAwayTableResults(
                        team_id=team.id,
                        competition_id=competition.id,
                        season=self.season
                    )
                # Map home columns
                home_map = {
                    'mp': 'home_mp', 'w': 'home_w', 'd': 'home_d', 'l': 'home_l',
                    'gf': 'home_gf', 'ga': 'home_ga', 'gd': 'home_gd', 'pts': 'home_pts',
                    'pts/mp': 'home_pts_per_mp', 'xg': 'home_xg', 'xga': 'home_xga',
                    'xgd': 'home_xgd', 'xgd/90': 'home_xgd_per_90'
                }
                for i in home_indices:
                    stat = header_stats[i].lower().strip()
                    key = home_map.get(stat)
                    if not key:
                        continue  # Skip columns not in the mapping
                    if key and hasattr(record, key):
                        setattr(record, key, self._parse_numeric_value(row[i]))
                # Map away columns
                away_map = {
                    'mp': 'away_mp', 'w': 'away_w', 'd': 'away_d', 'l': 'away_l',
                    'gf': 'away_gf', 'ga': 'away_ga', 'gd': 'away_gd', 'pts': 'away_pts',
                    'pts/mp': 'away_pts_per_mp', 'xg': 'away_xg', 'xga': 'away_xga',
                    'xgd': 'away_xgd', 'xgd/90': 'away_xgd_per_90'
                }
                for i in away_indices:
                    stat = header_stats[i].lower().strip()
                    key = away_map.get(stat)
                    if not key:
                        continue  # Skip columns not in the mapping
                    if key and hasattr(record, key):
                        setattr(record, key, self._parse_numeric_value(row[i]))
                if not existing:
                    db.add(record)
            db.commit()
            logger.info(f"Successfully saved home/away team stats for season {self.season}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving home/away team stats to database: {str(e)}")
            raise
        finally:
            db.close()

    async def scrape(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape all tables from the Premier League stats page and save to database.
        Returns a dictionary with table names as keys and table data as values.
        """
        try:
            html = await self.get_page_async(self.base_url)
            soup = self.parse_html(html)
            
            tables_data = self._extract_tables(soup)
            
            # Save team stats to database
            self._save_team_overall_table_results_to_db(tables_data)
            self._save_team_home_away_table_results_to_db(tables_data)
            
            return tables_data
            
        except Exception as e:
            self.logger.error(f"Error scraping FBref: {str(e)}")
            raise 