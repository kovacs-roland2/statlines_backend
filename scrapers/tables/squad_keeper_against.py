"""Squad keeper for table scraper."""

from typing import Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models import TeamSquadKeeperAgainst
from .base import BaseTableScraper
import logging

logger = logging.getLogger(__name__)

class SquadKeeperAgainstScraper(BaseTableScraper):
    """Scraper for squad keeper against table."""

    def _find_squad_keeper_table(self, tables_data: Dict[str, List[List[str]]]) -> Union[List[List[str]], None]:
        """Find the squad keeper against table in the data."""
        for table_name, table_data in tables_data.items():
            if 'stats_squads_keeper_against' in table_name.lower():
                return table_data
        logger.warning("Could not find squad keeper against table")
        return None

    def _map_row_to_stats(self, row: List[str], stats_record: TeamSquadKeeperAgainst, header_stats: List[str]) -> None:
        """Map row data to stats record fields."""
        # Create a mapping of header names to their indices
        header_map = {name.lower(): idx for idx, name in enumerate(header_stats)}

        # Map each stat to its corresponding field
        stats_record.player_number = self._parse_numeric_value(row[header_map.get('# pl', 1)])
        stats_record.age = self._parse_numeric_value(row[header_map.get('age', 1)])
        stats_record.matches_played = int(row[header_map.get('mp', 2)])
        stats_record.matches_started = int(row[header_map.get('starts', 3)])
        stats_record.minutes_played = int(row[header_map.get('min', 4)].replace(',', ''))
        stats_record.minutes_played_90s = self._parse_numeric_value(row[header_map.get('90s', 5)])
        stats_record.goals_against = int(row[header_map.get('ga', 6)])
        stats_record.goals_against_90s = self._parse_numeric_value(row[header_map.get('ga90', 7)])
        stats_record.shot_on_target_against = int(row[header_map.get('sota', 8)])
        stats_record.saves = int(row[header_map.get('saves', 9)])
        stats_record.save_percentage = self._parse_numeric_value(row[10])
        stats_record.wins = int(row[header_map.get('w', 11)])
        stats_record.draws = int(row[header_map.get('d', 12)])
        stats_record.losses = int(row[header_map.get('l', 13)])
        stats_record.clean_sheets = int(row[header_map.get('cs', 14)])
        stats_record.clean_sheets_percentage = self._parse_numeric_value(row[header_map.get('cs%', 15)])
        stats_record.penalties_attempted = int(row[header_map.get('pkatt', 16)])
        stats_record.penalties_allowed = int(row[header_map.get('pka', 17)])
        stats_record.penalties_saved = int(row[header_map.get('pksv', 18)])
        stats_record.penalties_missed = int(row[header_map.get('pkm', 19)])
        stats_record.penalties_saved_percentage = self._parse_numeric_value(row[20])

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save squad keeper against table data to database."""
        try:
            competition = self._get_or_create_competition(db)
            table = self._find_squad_keeper_table(tables_data)
            if not table or len(table) < 2:  # Need at least headers and one data row
                return

            header_stats = table[1]  # Get header row
            data_rows = table[2:]  # Skip header rows

            for row in data_rows:
                if len(row) < len(header_stats):  # Ensure we have enough columns
                    logger.warning(f"Row has fewer columns than header: {len(row)} vs {len(header_stats)}")
                    continue

                team = self._get_or_create_team(db, row[0].replace('vs ', ''), competition.id)
                existing_record = db.execute(
                    select(TeamSquadKeeperAgainst).where(
                        TeamSquadKeeperAgainst.team_id == team.id,
                        TeamSquadKeeperAgainst.season == self.season,
                        TeamSquadKeeperAgainst.competition_id == competition.id
                    )
                ).scalar_one_or_none()

                if existing_record:
                    record = existing_record
                else:
                    record = TeamSquadKeeperAgainst(
                        team_id=team.id,
                        competition_id=competition.id,
                        season=self.season
                    )

                self._map_row_to_stats(row, record, header_stats)

                if not existing_record:
                    db.add(record)

            db.commit()
            logger.info(f"Successfully saved squad keeper against stats for season {self.season}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving squad keeper against stats to database: {str(e)}")
            raise 