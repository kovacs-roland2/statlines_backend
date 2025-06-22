import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import sys
import os

# Add the parent directory to the path so we can import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session, create_tables
from database.models import Match, Team
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

def parse_date(date_str):
    """Parse date string from FBref format to date object."""
    if not date_str or date_str == '':
        return None
    
    try:
        # FBref uses format like "2024-08-16" or "Fri, Aug 16"
        if '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            # Handle format like "Fri, Aug 16"
            # We'll need to add the current year
            current_year = datetime.now().year
            date_with_year = f"{date_str}, {current_year}"
            return datetime.strptime(date_with_year, '%a, %b %d, %Y').date()
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'")
        return None

def parse_time(time_str):
    """Parse time string to time object."""
    if not time_str or time_str == '':
        return None
    
    try:
        # Handle format like "15:00"
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        print(f"Warning: Could not parse time '{time_str}'")
        return None

def parse_attendance(attendance_str):
    """Parse attendance string, handling commas and converting to integer"""
    if not attendance_str or attendance_str.strip() == '':
        return None
    
    try:
        # Remove commas and convert to integer
        clean_attendance = attendance_str.replace(',', '').strip()
        return int(clean_attendance)
    except (ValueError, AttributeError):
        return None

def find_team_by_name(session, team_name):
    """Find team by name, trying both full name and short name."""
    if not team_name:
        return None
    
    # First try exact match on name
    team = session.query(Team).filter(Team.name == team_name).first()
    if team:
        return team
    
    # Try partial match (case-insensitive)
    team = session.query(Team).filter(Team.name.ilike(f'%{team_name}%')).first()
    if team:
        return team
    
    # Try short name match
    team = session.query(Team).filter(Team.short_name == team_name).first()
    if team:
        return team
    
    print(f"Warning: Could not find team '{team_name}'")
    return None

def parse_score(score_str):
    """Parse score string like '2–1' or '2-1' to tuple of integers."""
    if not score_str or score_str == '':
        return None, None
    
    try:
        # Handle different dash characters
        score_str = score_str.replace('–', '-').replace('—', '-')
        if '-' in score_str:
            home_score, away_score = score_str.split('-')
            return int(home_score.strip()), int(away_score.strip())
    except (ValueError, AttributeError):
        pass
    
    return None, None

def get_team_id_by_name(team_name, session):
    """Get team ID by name, with fuzzy matching for common variations"""
    if not team_name:
        return None
    
    # Direct mapping for common team name variations
    team_name_mapping = {
        'Arsenal': 'Arsenal',
        'Aston Villa': 'Aston Villa', 
        'Bournemouth': 'Bournemouth',
        'Brentford': 'Brentford',
        'Brighton & Hove Albion': 'Brighton & Hove Albion',
        'Brighton': 'Brighton & Hove Albion',
        'Chelsea': 'Chelsea',
        'Crystal Palace': 'Crystal Palace',
        'Everton': 'Everton',
        'Fulham': 'Fulham',
        'Liverpool': 'Liverpool',
        'Manchester City': 'Manchester City',
        'Tottenham Hotspur': 'Tottenham Hotspur',
        'Tottenham': 'Tottenham Hotspur',
        'West Ham United': 'West Ham United',
        'West Ham': 'West Ham United',
        # Map scraped names to database names
        'Leicester City': 'Leicester City',  # Not in current database
        'Nott\'ham Forest': 'Nottingham Forest',
        'Nottingham Forest': 'Nottingham Forest', 
        'Newcastle Utd': 'Newcastle United',
        'Newcastle United': 'Newcastle United',
        'Southampton': 'Southampton',  # Not in current database
        'Ipswich Town': 'Ipswich Town',  # Not in current database
        'Wolves': 'Wolverhampton Wanderers',
        'Wolverhampton Wanderers': 'Wolverhampton Wanderers',
        'Manchester Utd': 'Manchester United',
        'Manchester United': 'Manchester United'
    }
    
    # Use mapping if available
    mapped_name = team_name_mapping.get(team_name, team_name)
    
    # Try to find team by mapped name
    team = session.query(Team).filter(Team.name == mapped_name).first()
    if team:
        return team.id
    
    # Try to find by original name if mapping didn't work
    team = session.query(Team).filter(Team.name == team_name).first()
    if team:
        return team.id
    
    return None

def validate_match_data(match_data, session):
    """Validate match data and return team IDs and parsed date."""
    home_team_id = get_team_id_by_name(match_data.get('home_team'), session)
    away_team_id = get_team_id_by_name(match_data.get('away_team'), session)
    
    if not home_team_id or not away_team_id:
        print(f"Skipping match: {match_data.get('home_team')} vs {match_data.get('away_team')} - teams not found")
        return None, None, None
    
    match_date = parse_date(match_data.get('date'))
    if not match_date:
        print(f"Skipping match: Invalid date {match_data.get('date')}")
        return None, None, None
    
    return home_team_id, away_team_id, match_date

def update_existing_match(existing_match, match_data, week_number, attendance):
    """Update an existing match with new data."""
    existing_match.week_number = week_number
    existing_match.match_time = parse_time(match_data.get('match_time'))
    existing_match.venue = match_data.get('venue')
    existing_match.referee = match_data.get('referee')
    existing_match.attendance = attendance
    
    home_score, away_score = parse_score(match_data.get('score'))
    if home_score is not None and away_score is not None:
        existing_match.home_score = home_score
        existing_match.away_score = away_score
    
    # Update xG if available
    if match_data.get('home_xg'):
        try:
            existing_match.home_xg = float(match_data.get('home_xg'))
        except ValueError:
            pass
    
    if match_data.get('away_xg'):
        try:
            existing_match.away_xg = float(match_data.get('away_xg'))
        except ValueError:
            pass
    
    existing_match.scraped_at = func.now()

def create_new_match(match_data, week_number, match_date, home_team_id, away_team_id, attendance):
    """Create a new match object."""
    home_score, away_score = parse_score(match_data.get('score'))
    
    new_match = Match(
        week_number=week_number,
        match_date=match_date,
        match_time=parse_time(match_data.get('match_time')),
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=home_score,
        away_score=away_score,
        venue=match_data.get('venue'),
        referee=match_data.get('referee'),
        attendance=attendance
    )
    
    # Add xG if available
    if match_data.get('home_xg'):
        try:
            new_match.home_xg = float(match_data.get('home_xg'))
        except ValueError:
            pass
    
    if match_data.get('away_xg'):
        try:
            new_match.away_xg = float(match_data.get('away_xg'))
        except ValueError:
            pass
    
    return new_match

def save_match_to_db(session, match_data):
    """Save or update a match in the database."""
    try:
        attendance = parse_attendance(match_data.get('attendance'))
        
        # Validate data and get team IDs
        home_team_id, away_team_id, match_date = validate_match_data(match_data, session)
        if not all([home_team_id, away_team_id, match_date]):
            return False
        
        # Parse week number
        week_number = None
        if match_data.get('week_number'):
            try:
                week_number = int(match_data.get('week_number'))
            except (ValueError, TypeError):
                pass
        
        # Check if match already exists
        existing_match = session.query(Match).filter(
            Match.match_date == match_date,
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id
        ).first()
        
        if existing_match:
            update_existing_match(existing_match, match_data, week_number, attendance)
        else:
            new_match = create_new_match(match_data, week_number, match_date, home_team_id, away_team_id, attendance)
            session.add(new_match)
        
        session.commit()
        return True
        
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        session.rollback()
        return False
    except Exception as e:
        print(f"Error saving match: {e}")
        return False

def get_match_results():
    """Scrape Premier League match results from FBref and save to database."""
    url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Initialize database
        create_tables()
        session = get_db_session()
        
        # Add a small delay
        time.sleep(2)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find the schedule table dynamically - look for table with ID starting with 'sched'
        table = None
        
        # Method 1: Find table with ID containing 'sched'
        schedule_tables = soup.find_all('table', id=lambda x: x and x.startswith('sched'))
        if schedule_tables:
            table = schedule_tables[0]  # Take the first schedule table
        
        # Method 2: Fallback - look for table with class 'stats_table' that has schedule data
        if not table:
            stats_tables = soup.find_all('table', class_='stats_table')
            for t in stats_tables:
                # Check if this table has typical schedule headers
                if t.find('th', string=lambda text: text and any(word in text.lower() for word in ['date', 'home', 'away', 'score'])):
                    table = t
                    break
        
        if not table:
            raise ValueError("Schedule table not found - the page structure may have changed")
        
        # Extract headers - only get the visible headers
        headers_list = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            # Skip hidden headers
            if 'data-stat' in th.attrs:
                headers_list.append(th.get('data-stat'))
        
        # Extract rows and save to database
        matches_processed = 0
        matches_saved = 0
        
        for tr in table.find('tbody').find_all('tr'):
            row_data = {}
            cells = tr.find_all(['td', 'th'])
            
            for i, td in enumerate(cells):
                if 'data-stat' in td.attrs and i < len(headers_list):
                    stat_name = td.get('data-stat')
                    
                    # Get the text content
                    text = td.get_text(strip=True)
                    
                    # For team names, get the full name from the link if available
                    if td.find('a') and stat_name in ['home_team', 'away_team']:
                        text = td.find('a').get_text(strip=True)
                    
                    row_data[stat_name] = text if text else None
            
            if row_data and row_data.get('home_team') and row_data.get('away_team'):
                matches_processed += 1
                
                # Map FBref column names to our expected format
                match_data = {
                    'week_number': row_data.get('gameweek'),
                    'date': row_data.get('date'),
                    'match_time': row_data.get('start_time'),
                    'home_team': row_data.get('home_team'),
                    'away_team': row_data.get('away_team'),
                    'score': row_data.get('score'),
                    'venue': row_data.get('venue'),
                    'referee': row_data.get('referee'),
                    'attendance': row_data.get('attendance'),
                    'home_xg': row_data.get('home_xg'),
                    'away_xg': row_data.get('away_xg')
                }
                
                if save_match_to_db(session, match_data):
                    matches_saved += 1
        
        session.close()
        
        print("Scraping completed!")
        print(f"Matches processed: {matches_processed}")
        print(f"Matches saved/updated: {matches_saved}")
        
        return matches_processed, matches_saved
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return 0, 0
    except Exception as e:
        print(f"Error processing the data: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

if __name__ == "__main__":
    print("StatLines Match Scraper")
    print("=" * 50)
    get_match_results() 