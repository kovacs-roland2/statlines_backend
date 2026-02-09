from fastapi import HTTPException
from sqlalchemy import or_, desc
from sqlalchemy.orm import joinedload
from database.models import Match, Team

def get_team_matches(session, team_name: str, limit: int):
    """
    Retrieve the last N matches for a specific team.
    
    Args:
        session: Database session
        team_name: Name of the team (case-insensitive, partial match supported)
        limit: Number of matches to return (1-20)
    
    Returns:
        Tuple of (team, matches) where team is the Team object and matches is a list of Match objects
    
    Raises:
        HTTPException: If team not found
    """
    # Find the team (case-insensitive partial match)
    team = session.query(Team).filter(
        or_(
            Team.name.ilike(f"%{team_name}%"),
            Team.short_name.ilike(f"%{team_name}%")
        )
    ).first()
    
    if not team:
        raise HTTPException(
            status_code=404, 
            detail=f"Team '{team_name}' not found. Please check the team name and try again."
        )
    
    # Get the team's matches (both home and away) with all related data
    matches = session.query(Match).options(
        joinedload(Match.home_team),
        joinedload(Match.away_team),
        joinedload(Match.competition)
    ).filter(
        or_(
            Match.home_team_id == team.id,
            Match.away_team_id == team.id
        )
    ).order_by(
        desc(Match.match_date),
        desc(Match.match_time)
    ).limit(limit).all()
    
    return team, matches