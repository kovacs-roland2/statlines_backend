#!/usr/bin/env python3
"""
Migration: Add team_squad_standard_for table for storing team squad standard statistics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

DESCRIPTION = "Add team_squad_standard_for table for storing team squad standard statistics including season and competition data."

def run_migration():
    session = get_db_session()
    try:
        print("Starting migration: Add team_squad_standard_for table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS team_squad_standard_for (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL REFERENCES competitions(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                season VARCHAR(20) NOT NULL,
                player_number NUMERIC(4, 1),
                age NUMERIC(4, 1),
                possession NUMERIC(4, 1),
                matches_played INTEGER,
                matches_started INTEGER,
                minutes_played INTEGER,
                minutes_played_90s NUMERIC(5, 1),
                goals INTEGER,
                assists INTEGER,
                goals_and_assists INTEGER,
                goals_minus_penalties INTEGER,
                penalties INTEGER,
                penalties_attempted INTEGER,
                yellow_cards INTEGER,
                red_cards INTEGER,
                expected_goals NUMERIC(6, 2),
                non_penalty_expected_goals NUMERIC(6, 2),
                expected_assisted_goals NUMERIC(6, 2),
                npxg_plus_xag NUMERIC(6, 2),
                progressive_carries INTEGER,
                progressive_passes INTEGER,
                goals_per90 NUMERIC(8, 2),
                assists_per90 NUMERIC(8, 2),
                goals_and_assists_per90 NUMERIC(8, 2),
                goals_minus_penalties_per90 NUMERIC(8, 2),
                goals_and_assists_minus_penalties_per90 NUMERIC(8, 2),
                expected_goals_per90 NUMERIC(8, 2),
                expected_assisted_goals_per90 NUMERIC(8, 2),
                expected_goals_and_assists_per90 NUMERIC(8, 2),
                non_penalty_expected_goals_per90 NUMERIC(8, 2),
                npxg_plus_xag_per90 NUMERIC(8, 2),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()
        print("Table created.")

        print("Adding indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_team_squad_standard_for_competition ON team_squad_standard_for(competition_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_standard_for_team ON team_squad_standard_for(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_standard_for_season ON team_squad_standard_for(season)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_standard_for_unique ON team_squad_standard_for(team_id, season, competition_id)"
        ]
        for index_sql in indexes:
            try:
                session.execute(text(index_sql))
                session.commit()
            except Exception as e:
                session.rollback()
                if "already exists" in str(e).lower():
                    print(f"Index already exists: {index_sql}")
                else:
                    raise e

        print("Adding unique constraint...")
        try:
            session.execute(text("""
                ALTER TABLE team_squad_standard_for 
                ADD CONSTRAINT uk_team_squad_standard_for_unique 
                UNIQUE (team_id, season, competition_id)
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Unique constraint already exists")
            else:
                raise e

        print("Adding updated_at trigger...")
        try:
            session.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """))
            session.execute(text("""
                CREATE TRIGGER update_team_squad_standard_for_updated_at 
                BEFORE UPDATE ON team_squad_standard_for 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Trigger already exists")
            else:
                print(f"Warning: Could not create trigger: {e}")

        print("Verifying migration...")
        table_exists = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'team_squad_standard_for'
            )
        """)).scalar()
        if table_exists:
            print("team_squad_standard_for table created successfully!")
        else:
            raise Exception("team_squad_standard_for table was not created")
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 