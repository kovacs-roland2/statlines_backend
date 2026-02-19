"""Overall results table scraper."""

from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models import TeamOverallTableResults
from .base import BaseTableScraper
import logging

logger = logging.getLogger(__name__)

class OverallResultsTableScraper(BaseTableScraper):
    """Scraper for overall results table."""

    def _find_overall_table(self, tables_data: Dict[str, List[List[str]]]) -> List[List[str]]:
        """Find the overall results table in the data."""
        for table_name, table_data in tables_data.items():
            if 'overall' in table_name.lower() and 'results' in table_name.lower():
                return table_data
        logger.warning("Could not find overall results table")
        return None
    
    def _map_row_to_stats(self, row: List[str], stats_record: TeamOverallTableResults) -> None:
        """Map row data to stats record fields."""
        stats_record.rk = int(row[0]) if row[0].isdigit() else None
        stats_record.squad = row[1]
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

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save overall results table data to database."""
        try:
            # Get or create competition
            competition = self._get_or_create_competition(db)
            
            # Find the overall results table
            overall_table = self._find_overall_table(tables_data)
            if not overall_table:
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
                self._map_row_to_stats(row, stats_record)
                
                if not existing_stats:
                    db.add(stats_record)
            
            db.commit()
            logger.info(f"Successfully saved overall team stats for season {self.season}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving overall team stats to database: {str(e)}")
            raise 