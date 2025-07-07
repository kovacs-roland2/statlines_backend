"""Migration to remove penalties_saved_percentage from team_squad_keeper_adv_for table."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

DESCRIPTION = "Remove penalties_saved_percentage column from team_squad_keeper_adv_for table."

def run_migration() -> None:
    session = get_db_session()
    try:
        print("Starting migration: Remove penalties_saved_percentage column...")
        
        # Check if column exists first
        column_exists = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'team_squad_keeper_adv_for'
                AND column_name = 'penalties_saved_percentage'
            )
        """)).scalar()
        
        if column_exists:
            session.execute(text("""
                ALTER TABLE team_squad_keeper_adv_for
                DROP COLUMN penalties_saved_percentage;
            """))
            session.commit()
            print("Column removed successfully!")
        else:
            print("Column penalties_saved_percentage does not exist, skipping...")
        
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 