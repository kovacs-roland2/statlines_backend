"""Base class for table-specific scrapers."""

from sqlalchemy.orm import Session
from database.models import Competition, Team
from sqlalchemy import select
from common.mappings.teams import get_standardized_team_name
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
        # Get standardized team name
        standardized_name = get_standardized_team_name(team_name)
        
        # First try to find team by standardized name
        team = db.execute(
            select(Team).where(Team.name == standardized_name)
        ).scalar_one_or_none()
        
        if not team:
            team = Team(
                name=standardized_name,  # Use standardized name for new teams
                competition_id=competition_id
            )
            db.add(team)
            db.commit()
            db.refresh(team)
            logger.info(f"Created new team: {standardized_name}")
        
        return team

    def _parse_numeric_value(self, value: str) -> float:
        """Parse value to float or None if it's not a number."""
        if not value or value == '':
            return None
        
        # Remove any '+' signs and convert to float
        value = value.replace('+', '').replace(',', '')
        try:
            return float(value)
        except ValueError:
            return None
