"""Team name mappings for standardization across different data sources."""

PREMIER_LEAGUE_TEAM_NAMES = {
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

def get_standardized_team_name(team_name: str, competition: str = 'Premier League') -> str:
    """
    Get the standardized team name based on various possible input names.
    
    Args:
        team_name: The team name to standardize
        competition: The competition context (defaults to Premier League)
        
    Returns:
        The standardized team name, or the original name if no mapping exists
    """
    if not team_name:
        return None
        
    if competition == 'Premier League':
        return PREMIER_LEAGUE_TEAM_NAMES.get(team_name, team_name)
        
    # Add mappings for other competitions here as needed
    return team_name 