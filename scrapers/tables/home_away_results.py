"""Home/Away results table scraper."""

from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models import TeamHomeAwayTableResults
from .base import BaseTableScraper
import logging

logger = logging.getLogger(__name__)

class HomeAwayResultsTableScraper(BaseTableScraper):
    """Scraper for home/away results table."""

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save home/away results table data to database."""
        try:
            # Get or create competition
            competition = self._get_or_create_competition(db)
            
            # Find the home/away table
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
            
            # Define column ranges for home and away stats
            home_indices = [i for i in range(2, 15)]
            away_indices = [i for i in range(15, 28)]
            
            # For each row, parse home and away stats
            for row in data_rows:
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