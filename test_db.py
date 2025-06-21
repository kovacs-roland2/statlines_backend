#!/usr/bin/env python3
"""
Test script to verify database setup and connection.
Run this after starting PostgreSQL with: docker-compose up -d
"""

import sys
from database import create_tables, get_db_session, Team, Match
from sqlalchemy.exc import OperationalError

def test_database_connection():
    """Test database connection and setup."""
    try:
        print("🔄 Testing database connection...")
        
        # Test connection
        db = get_db_session()
        
        # Create tables (SQLAlchemy models)
        print("🔄 Creating tables with SQLAlchemy...")
        create_tables()
        
        # Test basic operations
        print("🔄 Testing basic operations...")
        
        # Check if teams exist
        teams_count = db.query(Team).count()
        print(f"✅ Found {teams_count} teams in database")
        
        # Get a sample team
        if teams_count > 0:
            sample_team = db.query(Team).first()
            print(f"✅ Sample team: {sample_team.name} ({sample_team.short_name})")
        
        # Check matches
        matches_count = db.query(Match).count()
        print(f"✅ Found {matches_count} matches in database")
        
        print("✅ Database setup successful!")
        return True
        
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def add_sample_match():
    """Add a sample match to test the database."""
    try:
        db = get_db_session()
        
        # Get Arsenal and Liverpool
        arsenal = db.query(Team).filter(Team.name == "Arsenal").first()
        liverpool = db.query(Team).filter(Team.name == "Liverpool").first()
        
        if not arsenal or not liverpool:
            print("❌ Arsenal or Liverpool not found in database")
            return False
        
        # Check if this match already exists
        existing_match = db.query(Match).filter(
            Match.home_team_id == arsenal.id,
            Match.away_team_id == liverpool.id
        ).first()
        
        if existing_match:
            print(f"✅ Sample match already exists: {arsenal.name} {existing_match.result} {liverpool.name}")
            return True
        
        # Create a sample match
        from datetime import date, time
        sample_match = Match(
            week_number=1,
            match_date=date(2024, 8, 17),
            match_time=time(15, 0),
            home_team_id=arsenal.id,
            away_team_id=liverpool.id,
            home_score=2,
            away_score=1,
            home_xg=1.8,
            away_xg=1.2,
            venue="Emirates Stadium",
            attendance=60000,
            referee="Michael Oliver"
        )
        
        db.add(sample_match)
        db.commit()
        
        print(f"✅ Added sample match: {arsenal.name} {sample_match.result} {liverpool.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding sample match: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 StatLines Database Test")
    print("=" * 50)
    
    if test_database_connection():
        print("\n🔄 Adding sample match...")
        add_sample_match()
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Database tests failed!")
        sys.exit(1) 