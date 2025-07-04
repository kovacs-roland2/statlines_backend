#!/usr/bin/env python3
"""
Migration: Add team_squad_keeper_against table for storing team squad keeper statistics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

DESCRIPTION = "Add team_squad_keeper_against table for storing team squad keeper statistics including season and competition data."

def run_migration():
    session = get_db_session()
    try:
        print("Starting migration: Add team_squad_keeper_against table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS team_squad_keeper_against (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL REFERENCES competitions(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                season VARCHAR(20) NOT NULL,
                player_number NUMERIC(4, 1),
                matches_played INTEGER,
                matches_started INTEGER,
                minutes_played INTEGER,
                minutes_played_90s NUMERIC(5, 1),
                goals_against INTEGER,
                goals_against_90s NUMERIC(6, 2),
                shot_on_target_against INTEGER,
                saves INTEGER,
                save_percentage NUMERIC(6, 2),
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                clean_sheets INTEGER,
                clean_sheets_percentage NUMERIC(5, 1),
                penalties_attempted INTEGER,
                penalties_allowed INTEGER,
                penalties_saved INTEGER,
                penalties_missed INTEGER,
                penalties_saved_percentage NUMERIC(5, 1),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()
        print("Table created.")

        print("Adding indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_against_competition ON team_squad_keeper_against(competition_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_against_team ON team_squad_keeper_against(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_against_season ON team_squad_keeper_against(season)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_against_unique ON team_squad_keeper_against(team_id, season, competition_id)"
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
                ALTER TABLE team_squad_keeper_against
                ADD CONSTRAINT uk_team_squad_standard_keeper_against
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
                CREATE TRIGGER update_team_squad_keeper_against_updated_at 
                BEFORE UPDATE ON team_squad_keeper_against
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
                AND table_name = 'team_squad_keeper_against'
            )
        """)).scalar()
        if table_exists:
            print("team_squad_keeper_against table created successfully!")
        else:
            raise Exception("team_squad_keeper_against table was not created")
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 