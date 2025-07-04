"""Squad standard against table scraper."""

from typing import Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models import TeamSquadStandardAgainst
from .base import BaseTableScraper
import logging

logger = logging.getLogger(__name__)

class SquadStandardAgainstScraper(BaseTableScraper):
    """Scraper for squad standard against table."""

    def _find_squad_standard_table(self, tables_data: Dict[str, List[List[str]]]) -> Union[List[List[str]], None]:
        """Find the squad standard against table in the data."""
        for table_name, table_data in tables_data.items():
            if 'stats_squads_standard_against' in table_name.lower():
                return table_data
        logger.warning("Could not find squad standard against table")
        return None

    def _map_row_to_stats(self, row: List[str], stats_record: TeamSquadStandardAgainst, header_stats: List[str]) -> None:
        """Map row data to stats record fields."""
        # Create a mapping of header names to their indices
        header_map = {name.lower(): idx for idx, name in enumerate(header_stats)}

        # Map each stat to its corresponding field
        stats_record.player_number = self._parse_numeric_value(row[header_map.get('# pl', 1)])
        stats_record.age = self._parse_numeric_value(row[header_map.get('age', 1)])
        stats_record.possession = self._parse_numeric_value(row[header_map.get('poss', 2)])
        stats_record.matches_played = int(row[header_map.get('mp', 3)])
        stats_record.matches_started =int(row[header_map.get('starts', 3)])
        stats_record.minutes_played = int(row[header_map.get('min', 5)].replace(',', ''))
        stats_record.minutes_played_90s = self._parse_numeric_value(row[header_map.get('90s', 6)])
        stats_record.goals = int(row[8])
        stats_record.assists = int(row[9])
        stats_record.goals_and_assists = int(row[10])
        stats_record.goals_minus_penalties = int(row[11])
        stats_record.penalties = int(row[header_map.get('pk', 11)])
        stats_record.penalties_attempted = int(row[header_map.get('pkatt', 12)])
        stats_record.yellow_cards = int(row[header_map.get('crdy', 13)])
        stats_record.red_cards = int(row[header_map.get('crdr', 14)])
        stats_record.expected_goals = self._parse_numeric_value(row[16])
        stats_record.non_penalty_expected_goals = self._parse_numeric_value(row[17])
        stats_record.expected_assisted_goals = self._parse_numeric_value(row[18])
        stats_record.npxg_plus_xag = self._parse_numeric_value(row[19])
        stats_record.progressive_carries = int(row[20])
        stats_record.progressive_passes = int(row[21])
        stats_record.goals_per90 = self._parse_numeric_value(row[22])
        stats_record.assists_per90 = self._parse_numeric_value(row[23])
        stats_record.goals_and_assists_per90 = self._parse_numeric_value(row[24])
        stats_record.goals_minus_penalties_per90 = self._parse_numeric_value(row[25])
        stats_record.goals_and_assists_minus_penalties_per90 = self._parse_numeric_value(row[26])
        stats_record.expected_goals_per90 = self._parse_numeric_value(row[27])
        stats_record.expected_assisted_goals_per90 = self._parse_numeric_value(row[28])
        stats_record.expected_goals_and_assists_per90 = self._parse_numeric_value(row[29])
        stats_record.non_penalty_expected_goals_per90 = self._parse_numeric_value(row[30])
        stats_record.npxg_plus_xag_per90 = self._parse_numeric_value(row[31])

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save squad standard agaisnt table data to database."""
        try:
            competition = self._get_or_create_competition(db)
            table = self._find_squad_standard_table(tables_data)
            if not table or len(table) < 2:  # Need at least headers and one data row
                return

            header_stats = table[1]
            data_rows = table[2:]
            for row in data_rows:
                if len(row) < len(header_stats):  # Ensure we have enough columns
                    logger.warning(f"Row has fewer columns than header: {len(row)} vs {len(header_stats)}")
                    continue

                team = self._get_or_create_team(db, row[0].replace('vs ', ''), competition.id)
                existing_record = db.execute(
                    select(TeamSquadStandardAgainst).where(
                        TeamSquadStandardAgainst.team_id == team.id,
                        TeamSquadStandardAgainst.season == self.season,
                        TeamSquadStandardAgainst.competition_id == competition.id
                    )
                ).scalar_one_or_none()

                if existing_record:
                    record = existing_record
                else:
                    record = TeamSquadStandardAgainst(
                        team_id=team.id,
                        competition_id=competition.id,
                        season=self.season
                    )

                self._map_row_to_stats(row, record, header_stats)

                if not existing_record:
                    db.add(record)

            db.commit()
            logger.info(f"Successfully saved squad standard against stats for season {self.season}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving squad standard against stats to database: {str(e)}")
            raise 