#!/usr/bin/env python3
"""
Migration: Add competition_id to teams table for multi-league team support.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

# Migration metadata
DESCRIPTION = "Add competition_id column to teams table to associate teams with specific competitions/leagues"

def run_migration():
    """Add competition_id column to teams table."""
    session = get_db_session()
    
    try:
        print("Starting migration: Add competition_id to teams...")
        
        # Add competition_id column to teams table
        print("Adding competition_id column to teams table...")
        try:
            session.execute(text("ALTER TABLE teams ADD COLUMN competition_id INTEGER"))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("competition_id column already exists")
            else:
                raise e
        
        # Add foreign key constraint
        print("Adding foreign key constraint...")
        try:
            session.execute(text("""
                ALTER TABLE teams 
                ADD CONSTRAINT fk_teams_competition 
                FOREIGN KEY (competition_id) REFERENCES competitions(id)
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Foreign key constraint already exists")
            else:
                raise e
        
        # Add index for performance
        print("Adding index on competition_id...")
        try:
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_teams_competition ON teams(competition_id)"))
            session.commit()
        except Exception:
            session.rollback()
        
        # Update existing teams to Premier League (fbref_id = 9)
        print("Updating existing teams to Premier League...")
        result = session.execute(text("""
            UPDATE teams 
            SET competition_id = (SELECT id FROM competitions WHERE fbref_id = 9)
            WHERE competition_id IS NULL
        """))
        print(f"Updated {result.rowcount} teams")
        session.commit()
        
        # Verify the changes
        print("Verifying migration...")
        teams_with_competition = session.execute(text("SELECT COUNT(*) FROM teams WHERE competition_id IS NOT NULL")).scalar()
        total_teams = session.execute(text("SELECT COUNT(*) FROM teams")).scalar()
        
        print(f"{teams_with_competition}/{total_teams} teams have competition assigned")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 