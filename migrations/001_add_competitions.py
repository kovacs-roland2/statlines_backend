#!/usr/bin/env python3
"""
Migration: Add competitions table and competition_id to matches table.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

# Migration metadata
DESCRIPTION = "Add competitions table and competition_id column to matches table for multi-league support"

def run_migration():
    """Add competitions table and competition_id column to matches."""
    session = get_db_session()
    
    try:
        print("Starting migration: Add competitions support...")
        
        # Create competitions table
        print("Creating competitions table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS competitions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                short_name VARCHAR(20),
                country VARCHAR(50),
                fbref_id INTEGER UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        session.commit()
        
        # Add competition_id column to matches table
        print("Adding competition_id column to matches table...")
        try:
            session.execute(text("ALTER TABLE matches ADD COLUMN competition_id INTEGER"))
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
                ALTER TABLE matches 
                ADD CONSTRAINT fk_matches_competition 
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
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition_id)"))
            session.commit()
        except Exception:
            session.rollback()
        
        # Insert initial competitions
        print("Adding initial competitions...")
        competitions_data = [
            (9, 'Premier League', 'EPL', 'England'),
            (12, 'La Liga', 'LaLiga', 'Spain'),
            (20, 'Bundesliga', 'BUN', 'Germany'),
            (11, 'Serie A', 'SerieA', 'Italy'),
            (13, 'Ligue 1', 'L1', 'France'),
        ]
        
        for fbref_id, name, short_name, country in competitions_data:
            session.execute(text("""
                INSERT INTO competitions (fbref_id, name, short_name, country) 
                VALUES (:fbref_id, :name, :short_name, :country) 
                ON CONFLICT (fbref_id) DO NOTHING
            """), {
                'fbref_id': fbref_id,
                'name': name, 
                'short_name': short_name,
                'country': country
            })
        session.commit()
        
        # Update existing matches to Premier League (fbref_id = 9)
        print("Updating existing matches to Premier League...")
        result = session.execute(text("""
            UPDATE matches 
            SET competition_id = (SELECT id FROM competitions WHERE fbref_id = 9)
            WHERE competition_id IS NULL
        """))
        print(f"Updated {result.rowcount} matches")
        session.commit()
        
        # Verify the changes
        print("Verifying migration...")
        competitions_count = session.execute(text("SELECT COUNT(*) FROM competitions")).scalar()
        matches_with_competition = session.execute(text("SELECT COUNT(*) FROM matches WHERE competition_id IS NOT NULL")).scalar()
        
        print(f"{competitions_count} competitions in database")
        print(f"{matches_with_competition} matches have competition assigned")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 