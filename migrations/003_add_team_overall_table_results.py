#!/usr/bin/env python3
"""
Migration: Add team_overall_table_results table for storing team overall table results data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

# Migration metadata
DESCRIPTION = "Add team_overall_table_results table for storing overall team statistics including season and competition data"

def run_migration():
    """Add team_overall_table_results table to store team statistics."""
    session = get_db_session()
    
    try:
        print("Starting migration: Add team_overall_table_results table...")
        
        # Create team_overall_table_results table
        print("Creating team_overall_table_results table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS team_overall_table_results (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL REFERENCES competitions(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                season VARCHAR(20) NOT NULL,
                rk INTEGER,
                squad VARCHAR(100) NOT NULL,
                mp INTEGER,
                w INTEGER,
                d INTEGER,
                l INTEGER,
                gf INTEGER,
                ga INTEGER,
                gd INTEGER,
                pts INTEGER,
                pts_per_mp NUMERIC(4, 2),
                xg NUMERIC(5, 2),
                xga NUMERIC(5, 2),
                xgd NUMERIC(5, 2),
                xgd_per_90 NUMERIC(4, 3),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()
        
        # Add indexes for performance
        print("Adding indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_team_overall_table_results_competition ON team_overall_table_results(competition_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_overall_table_results_team ON team_overall_table_results(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_overall_table_results_season ON team_overall_table_results(season)",
            "CREATE INDEX IF NOT EXISTS idx_team_overall_table_results_unique ON team_overall_table_results(team_id, season, competition_id)"
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
        
        # Add unique constraint to prevent duplicate entries
        print("Adding unique constraint...")
        try:
            session.execute(text("""
                ALTER TABLE team_overall_table_results 
                ADD CONSTRAINT uk_team_overall_table_results_unique 
                UNIQUE (team_id, season, competition_id)
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Unique constraint already exists")
            else:
                raise e
        
        # Add trigger for updated_at timestamp
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
                CREATE TRIGGER update_team_overall_table_results_updated_at 
                BEFORE UPDATE ON team_overall_table_results 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Trigger already exists")
            else:
                print(f"Warning: Could not create trigger: {e}")
        
        # Verify the changes
        print("Verifying migration...")
        table_exists = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'team_overall_table_results'
            )
        """)).scalar()
        
        if table_exists:
            print("team_overall_table_results table created successfully!")
            
            # Check columns
            columns_result = session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'team_overall_table_results' 
                ORDER BY ordinal_position
            """))
            
            columns = columns_result.fetchall()
            print(f"Table has {len(columns)} columns:")
            for column_name, data_type in columns:
                print(f"  - {column_name}: {data_type}")
        else:
            raise Exception("team_overall_table_results table was not created")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 