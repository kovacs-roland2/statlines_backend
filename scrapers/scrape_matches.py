import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import sys
import os
import argparse

# Add the parent directory to the path so we can import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session, create_tables
from database.models import Match, Team, Competition
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

def get_team_id_by_name(team_name, session, competition_id=None):
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
        'Leicester City': 'Leicester City',
        'Nott\'ham Forest': 'Nottingham Forest',
        'Nottingham Forest': 'Nottingham Forest', 
        'Newcastle Utd': 'Newcastle United',
        'Newcastle United': 'Newcastle United',
        'Southampton': 'Southampton',
        'Ipswich Town': 'Ipswich Town',
        'Wolves': 'Wolverhampton Wanderers',
        'Wolverhampton Wanderers': 'Wolverhampton Wanderers',
        'Manchester Utd': 'Manchester United',
        'Manchester United': 'Manchester United'
    }
    
    # Use mapping if available
    mapped_name = team_name_mapping.get(team_name, team_name)
    
    # Try to find team by mapped name and competition
    query = session.query(Team).filter(Team.name == mapped_name)
    if competition_id:
        query = query.filter(Team.competition_id == competition_id)
    team = query.first()
    if team:
        return team.id
    
    # Try to find by original name if mapping didn't work
    query = session.query(Team).filter(Team.name == team_name)
    if competition_id:
        query = query.filter(Team.competition_id == competition_id)
    team = query.first()
    if team:
        return team.id
    
    return None

def validate_match_data(match_data, session, competition_id=None):
    """Validate match data and return team IDs and parsed date."""
    home_team_id = get_team_id_by_name(match_data.get('home_team'), session, competition_id)
    away_team_id = get_team_id_by_name(match_data.get('away_team'), session, competition_id)
    
    if not home_team_id or not away_team_id:
        print(f"Skipping match: {match_data.get('home_team')} vs {match_data.get('away_team')} - teams not found")
        return None, None, None
    
    match_date = parse_date(match_data.get('date'))
    if not match_date:
        print(f"Skipping match: Invalid date {match_data.get('date')}")
        return None, None, None
    
    return home_team_id, away_team_id, match_date

def update_existing_match(existing_match, match_data, week_number, attendance, competition_id=None):
    """Update an existing match with new data."""
    existing_match.week_number = week_number
    existing_match.match_time = parse_time(match_data.get('match_time'))
    existing_match.venue = match_data.get('venue')
    existing_match.referee = match_data.get('referee')
    existing_match.attendance = attendance
    
    # Update competition_id if provided
    if competition_id:
        existing_match.competition_id = competition_id
    
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

def create_new_match(match_data, week_number, match_date, home_team_id, away_team_id, attendance, competition_id=None):
    """Create a new match object."""
    home_score, away_score = parse_score(match_data.get('score'))
    
    new_match = Match(
        competition_id=competition_id,
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

def save_match_to_db(session, match_data, competition_id=None):
    """Save or update a match in the database."""
    try:
        attendance = parse_attendance(match_data.get('attendance'))
        
        # Validate data and get team IDs
        home_team_id, away_team_id, match_date = validate_match_data(match_data, session, competition_id)
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
        query = session.query(Match).filter(
            Match.match_date == match_date,
            Match.home_team_id == home_team_id,
            Match.away_team_id == away_team_id
        )
        if competition_id:
            query = query.filter(Match.competition_id == competition_id)
        existing_match = query.first()
        
        if existing_match:
            update_existing_match(existing_match, match_data, week_number, attendance, competition_id)
        else:
            new_match = create_new_match(match_data, week_number, match_date, home_team_id, away_team_id, attendance, competition_id)
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

def get_competition_url(competition_fbref_id):
    """Get the FBref URL for a given competition ID."""
    competition_urls = {
        9: "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
        12: "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures", 
        20: "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures",
        11: "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures",
        13: "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
    }
    return competition_urls.get(competition_fbref_id)

def find_schedule_table(soup):
    """Find the schedule table in the parsed HTML."""
    # Method 1: Find table with ID containing 'sched'
    schedule_tables = soup.find_all('table', id=lambda x: x and x.startswith('sched'))
    if schedule_tables:
        return schedule_tables[0]
    
    # Method 2: Fallback - look for table with class 'stats_table' that has schedule data
    stats_tables = soup.find_all('table', class_='stats_table')
    for t in stats_tables:
        if t.find('th', string=lambda text: text and any(word in text.lower() for word in ['date', 'home', 'away', 'score'])):
            return t
    
    return None

def extract_table_headers(table):
    """Extract headers from the schedule table."""
    headers_list = []
    header_row = table.find('thead').find('tr')
    for th in header_row.find_all('th'):
        if 'data-stat' in th.attrs:
            headers_list.append(th.get('data-stat'))
    return headers_list

def process_table_row(tr, headers_list):
    """Process a single table row and return match data."""
    row_data = {}
    cells = tr.find_all(['td', 'th'])
    
    for i, td in enumerate(cells):
        if 'data-stat' in td.attrs and i < len(headers_list):
            stat_name = td.get('data-stat')
            text = td.get_text(strip=True)
            
            # For team names, get the full name from the link if available
            if td.find('a') and stat_name in ['home_team', 'away_team']:
                text = td.find('a').get_text(strip=True)
            
            row_data[stat_name] = text if text else None
    
    if row_data and row_data.get('home_team') and row_data.get('away_team'):
        return {
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
    return None

def get_match_results(competition_fbref_id=9):
    """Scrape match results from FBref and save to database."""
    url = get_competition_url(competition_fbref_id)
    if not url:
        print(f"Error: Unsupported competition FBref ID: {competition_fbref_id}")
        return 0, 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        create_tables()
        session = get_db_session()
        
        # Get competition from database
        competition = session.query(Competition).filter(Competition.fbref_id == competition_fbref_id).first()
        if not competition:
            print(f"Error: Competition with FBref ID {competition_fbref_id} not found in database")
            return 0, 0
        
        print(f"Scraping {competition.name} (FBref ID: {competition_fbref_id})")
        
        # Fetch and parse the webpage
        time.sleep(2)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find and process the schedule table
        table = find_schedule_table(soup)
        if not table:
            raise ValueError("Schedule table not found - the page structure may have changed")
        
        headers_list = extract_table_headers(table)
        matches_processed = 0
        matches_saved = 0
        
        # Process each row in the table
        for tr in table.find('tbody').find_all('tr'):
            match_data = process_table_row(tr, headers_list)
            if match_data:
                matches_processed += 1
                if save_match_to_db(session, match_data, competition.id):
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
    parser = argparse.ArgumentParser(description='Scrape match data from FBref')
    parser.add_argument('--competition', type=int, default=9, 
                       help='FBref competition ID (9=Premier League, 12=La Liga, 20=Bundesliga, 11=Serie A, 13=Ligue 1)')
    
    args = parser.parse_args()
    
    print("StatLines Match Scraper")
    print("=" * 50)
    get_match_results(args.competition) 