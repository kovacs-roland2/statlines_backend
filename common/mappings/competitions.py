"""Competition mappings and constants."""

# FBref competition IDs
PREMIER_LEAGUE_ID = 9
LA_LIGA_ID = 12
BUNDESLIGA_ID = 20
SERIE_A_ID = 11
LIGUE_1_ID = 13

# Competition names
COMPETITION_NAMES = {
    PREMIER_LEAGUE_ID: "Premier League",
    LA_LIGA_ID: "La Liga",
    BUNDESLIGA_ID: "Bundesliga",
    SERIE_A_ID: "Serie A",
    LIGUE_1_ID: "Ligue 1"
}

# FBref URLs for competition schedules
COMPETITION_URLS = {
    PREMIER_LEAGUE_ID: "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
    LA_LIGA_ID: "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures",
    BUNDESLIGA_ID: "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures",
    SERIE_A_ID: "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures",
    LIGUE_1_ID: "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures"
}

def get_competition_url(competition_fbref_id: int) -> str:
    """
    Get the FBref URL for a given competition ID.
    
    Args:
        competition_fbref_id: The FBref ID for the competition
        
    Returns:
        The URL for the competition's schedule page, or None if not found
    """
    return COMPETITION_URLS.get(competition_fbref_id)

def get_competition_name(competition_fbref_id: int) -> str:
    """
    Get the standardized competition name for a given FBref ID.
    
    Args:
        competition_fbref_id: The FBref ID for the competition
        
    Returns:
        The standardized competition name, or None if not found
    """
    return COMPETITION_NAMES.get(competition_fbref_id) 