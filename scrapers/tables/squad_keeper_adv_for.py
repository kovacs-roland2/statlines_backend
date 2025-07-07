"""Squad keeper advanced for table scraper."""

from typing import Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.models import TeamSquadKeeperAdvFor
from .base import BaseTableScraper
import logging

logger = logging.getLogger(__name__)

class SquadKeeperAdvForScraper(BaseTableScraper):
    """Scraper for squad keeper advanced for table."""

    def _find_squad_keeper_adv_table(self, tables_data: Dict[str, List[List[str]]]) -> Union[List[List[str]], None]:
        """Find the squad keeper advanced for table in the data."""
        for table_name, table_data in tables_data.items():
            if 'stats_squads_keeper_adv_for' in table_name.lower():
                return table_data
        logger.warning("Could not find squad keeper advanced for table")
        return None

    def _map_row_to_stats(self, row: List[str], stats_record: TeamSquadKeeperAdvFor, header_stats: List[str]) -> None:
        """Map row data to stats record fields."""
        # Create a mapping of header names to their indices
        header_map = {name.lower(): idx for idx, name in enumerate(header_stats)}

        # Map each stat to its corresponding field
        stats_record.free_kick_goals_against = int(row[header_map.get('fk', 1)])
        stats_record.corner_kick_goals_against = int(row[header_map.get('ck', 2)])
        stats_record.own_goals_against = int(row[header_map.get('og', 3)])
        stats_record.post_shot_xg = self._parse_numeric_value(row[header_map.get('psxg', 4)])
        stats_record.post_shot_xg_per_shot_ot = self._parse_numeric_value(row[header_map.get('psxg/sot', 5)])
        stats_record.post_shot_xg_minus_goals_allowed = self._parse_numeric_value(row[10])
        stats_record.post_shot_xg_minus_goals_allowed_90s = self._parse_numeric_value(row[11])
        stats_record.completed_long_balls = int(row[header_map.get('cmp', 8)])
        stats_record.attempted_long_balls = int(row[13])
        stats_record.long_balls_completed_percentage = self._parse_numeric_value(row[header_map.get('cmp%', 10)])
        stats_record.passes_attempted = int(row[15])
        stats_record.throws_attempted = int(row[header_map.get('thr', 12)])
        stats_record.launch_percentage = self._parse_numeric_value(row[17])
        stats_record.avg_pass_length = self._parse_numeric_value(row[18])
        stats_record.goal_kicks = int(row[19])
        stats_record.goal_kicks_launched_percentage = self._parse_numeric_value(row[20])
        stats_record.goal_kicks_avg_length = self._parse_numeric_value(row[21])
        stats_record.crosses_faced = int(row[22])
        stats_record.crosses_stopped = int(row[header_map.get('stp', 19)])
        stats_record.crosses_stopped_percentage = self._parse_numeric_value(row[header_map.get('stp%', 20)])
        stats_record.def_actions_outside_of_penalty_area = int(row[25])
        stats_record.def_actions_outside_of_penalty_area_90s = self._parse_numeric_value(row[26])
        stats_record.avg_def_action_dist = self._parse_numeric_value(row[27])

    def save_to_db(self, tables_data: Dict[str, List[List[str]]], db: Session) -> None:
        """Save squad keeper advanced for table data to database."""
        try:
            competition = self._get_or_create_competition(db)
            table = self._find_squad_keeper_adv_table(tables_data)
            if not table or len(table) < 2:  # Need at least headers and one data row
                return

            header_stats = table[1]  # Get header row
            data_rows = table[2:]  # Skip header rows

            for row in data_rows:
                if len(row) < len(header_stats):  # Ensure we have enough columns
                    logger.warning(f"Row has fewer columns than header: {len(row)} vs {len(header_stats)}")
                    continue

                team = self._get_or_create_team(db, row[0], competition.id)
                existing_record = db.execute(
                    select(TeamSquadKeeperAdvFor).where(
                        TeamSquadKeeperAdvFor.team_id == team.id,
                        TeamSquadKeeperAdvFor.season == self.season,
                        TeamSquadKeeperAdvFor.competition_id == competition.id
                    )
                ).scalar_one_or_none()

                if existing_record:
                    record = existing_record
                else:
                    record = TeamSquadKeeperAdvFor(
                        team_id=team.id,
                        competition_id=competition.id,
                        season=self.season
                    )

                self._map_row_to_stats(row, record, header_stats)

                if not existing_record:
                    db.add(record)

            db.commit()
            logger.info(f"Successfully saved squad keeper advanced for stats for season {self.season}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving squad keeper advanced for stats to database: {str(e)}")
            raise 