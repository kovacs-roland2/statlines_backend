"""Base class for table-specific scrapers."""

from typing import Dict, List
from sqlalchemy.orm import Session
from database.models import Competition, Team
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class BaseTableScraper:
    """Base class for table-specific scrapers with common functionality."""

    def __init__(self, season: str, competition_name: str):
        self.season = season
        self.competition_name = competition_name

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

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save table data to database. To be implemented by child classes."""
        raise NotImplementedError("Child classes must implement save_to_db method.") 