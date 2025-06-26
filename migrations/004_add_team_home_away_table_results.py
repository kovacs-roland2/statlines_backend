#!/usr/bin/env python3
"""
Migration: Add team_home_away_table_results table for storing home/away split team statistics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

DESCRIPTION = "Add team_home_away_table_results table for storing home/away split team statistics including season and competition data."

def run_migration():
    session = get_db_session()
    try:
        print("Starting migration: Add team_home_away_table_results table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS team_home_away_table_results (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL REFERENCES competitions(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                season VARCHAR(20) NOT NULL,
                home_mp INTEGER,
                home_w INTEGER,
                home_d INTEGER,
                home_l INTEGER,
                home_gf INTEGER,
                home_ga INTEGER,
                home_gd INTEGER,
                home_pts INTEGER,
                home_pts_per_mp NUMERIC(4, 2),
                home_xg NUMERIC(5, 2),
                home_xga NUMERIC(5, 2),
                home_xgd NUMERIC(5, 2),
                home_xgd_per_90 NUMERIC(4, 3),
                away_mp INTEGER,
                away_w INTEGER,
                away_d INTEGER,
                away_l INTEGER,
                away_gf INTEGER,
                away_ga INTEGER,
                away_gd INTEGER,
                away_pts INTEGER,
                away_pts_per_mp NUMERIC(4, 2),
                away_xg NUMERIC(5, 2),
                away_xga NUMERIC(5, 2),
                away_xgd NUMERIC(5, 2),
                away_xgd_per_90 NUMERIC(4, 3),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()
        print("Table created.")

        print("Adding indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_team_home_away_table_results_competition ON team_home_away_table_results(competition_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_home_away_table_results_team ON team_home_away_table_results(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_home_away_table_results_season ON team_home_away_table_results(season)",
            "CREATE INDEX IF NOT EXISTS idx_team_home_away_table_results_unique ON team_home_away_table_results(team_id, season, competition_id)"
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
                ALTER TABLE team_home_away_table_results 
                ADD CONSTRAINT uk_team_home_away_table_results_unique 
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
                CREATE TRIGGER update_team_home_away_table_results_updated_at 
                BEFORE UPDATE ON team_home_away_table_results 
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
                AND table_name = 'team_home_away_table_results'
            )
        """)).scalar()
        if table_exists:
            print("team_home_away_table_results table created successfully!")
        else:
            raise Exception("team_home_away_table_results table was not created")
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 