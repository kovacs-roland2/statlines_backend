#!/usr/bin/env python3
"""
ONE-TIME Setup script for local PostgreSQL database
Run this ONCE after installing PostgreSQL locally on your Mac

NOTE: After running this script successfully, you can delete this file
as it's only needed for initial database setup.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def create_database():
    """Create the statlines_dev database if it doesn't exist."""
    try:
        # Connect to PostgreSQL (default postgres database)
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password=input("Enter your PostgreSQL password: "),
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='statlines_dev'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE statlines_dev")
            print("✅ Created database 'statlines_dev'")
        else:
            print("✅ Database 'statlines_dev' already exists")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_schema_and_data():
    """Set up the database schema and initial data."""
    try:
        # Get password from user
        password = input("Enter your PostgreSQL password: ")
        
        # Connect to the statlines_dev database
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password=password,
            database="statlines_dev"
        )
        cursor = conn.cursor()
        
        # Create teams table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                short_name VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                week_number INTEGER,
                match_date DATE NOT NULL,
                match_time TIME,
                home_team_id INTEGER REFERENCES teams(id),
                away_team_id INTEGER REFERENCES teams(id),
                home_score INTEGER,
                away_score INTEGER,
                home_xg NUMERIC(4, 2),
                away_xg NUMERIC(4, 2),
                venue VARCHAR(100),
                attendance INTEGER,
                referee VARCHAR(100),
                match_report_url TEXT,
                notes TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert Premier League teams
        teams_data = [
            ('Arsenal', 'ARS'),
            ('Aston Villa', 'AVL'),
            ('Bournemouth', 'BOU'),
            ('Brentford', 'BRE'),
            ('Brighton & Hove Albion', 'BHA'),
            ('Chelsea', 'CHE'),
            ('Crystal Palace', 'CRY'),
            ('Everton', 'EVE'),
            ('Fulham', 'FUL'),
            ('Liverpool', 'LIV'),
            ('Luton Town', 'LUT'),
            ('Manchester City', 'MCI'),
            ('Manchester United', 'MUN'),
            ('Newcastle United', 'NEW'),
            ('Nottingham Forest', 'NFO'),
            ('Sheffield United', 'SHU'),
            ('Tottenham Hotspur', 'TOT'),
            ('West Ham United', 'WHU'),
            ('Wolverhampton Wanderers', 'WOL'),
            ('Burnley', 'BUR')
        ]
        
        # Insert teams (ignore duplicates)
        for name, short_name in teams_data:
            cursor.execute("""
                INSERT INTO teams (name, short_name) 
                VALUES (%s, %s) 
                ON CONFLICT (name) DO NOTHING
            """, (name, short_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database schema and teams data set up successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up schema: {e}")
        return False

def update_env_file(password):
    """Update the .env.local file with the correct password."""
    try:
        with open('.env.local', 'r') as f:
            content = f.read()
        
        # Replace the placeholder password
        content = content.replace('your_password', password)
        
        with open('.env.local', 'w') as f:
            f.write(content)
            
        print("✅ Updated .env.local with your password")
        
    except Exception as e:
        print(f"❌ Error updating .env.local: {e}")

if __name__ == "__main__":
    print("🚀 StatLines Local Database Setup")
    print("=" * 50)
    
    print("\n1. Creating database...")
    if create_database():
        print("\n2. Setting up schema and data...")
        if setup_schema_and_data():
            password = input("\nEnter your PostgreSQL password to save in .env.local: ")
            update_env_file(password)
            print("\n✅ Local database setup complete!")
            print("\n📋 Next steps:")
            print("1. Copy .env.local to .env: cp .env.local .env")
            print("2. Test the connection: python test_db.py")
            print("3. Connect with DBeaver using:")
            print("   - Host: localhost")
            print("   - Port: 5432")
            print("   - Database: statlines_dev")
            print("   - User: postgres")
            print("   - Password: [your password]")
        else:
            sys.exit(1)
    else:
        sys.exit(1) 