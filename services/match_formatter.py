from typing import List
from database.models import Match, Team

def format_match_response(match: Match, team: Team) -> dict:
    """
    Format a single match object into a MatchResponse dictionary.
    
    Args:
        match: Match object from database
        team: Team object to determine if match is home or away
    
    Returns:
        Dictionary with formatted match data
    """
    is_home_match = match.home_team_id == team.id
    
    return {
        "id": match.id,
        "match_date": match.match_date,
        "match_time": match.match_time,
        "week_number": match.week_number,
        "home_team": {
            "id": match.home_team.id,
            "name": match.home_team.name,
            "short_name": match.home_team.short_name
        },
        "away_team": {
            "id": match.away_team.id,
            "name": match.away_team.name,
            "short_name": match.away_team.short_name
        },
        "home_score": match.home_score,
        "away_score": match.away_score,
        "home_xg": float(match.home_xg) if match.home_xg else None,
        "away_xg": float(match.away_xg) if match.away_xg else None,
        "venue": match.venue,
        "attendance": match.attendance,
        "referee": match.referee,
        "competition": match.competition.name if match.competition else "Unknown",
        "is_home_match": is_home_match
    }

def format_team_matches_response(team: Team, matches: List[Match]) -> dict:
    """
    Format a list of matches into a TeamMatchesResponse dictionary.
    
    Args:
        team: Team object
        matches: List of Match objects
    
    Returns:
        Dictionary with formatted team matches data
    """
    match_responses = [format_match_response(match, team) for match in matches]
    
    return {
        "team_name": team.name,
        "matches": match_responses,
        "total_matches_found": len(match_responses)
    }