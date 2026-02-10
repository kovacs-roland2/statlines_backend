from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, time

from services.team_rank import get_team_rank
from services.team_matches import get_team_matches
from services.match_formatter import format_team_matches_response
from database.config import get_db_session

# Create router for team-related endpoints
router = APIRouter(prefix="/api/teams", tags=["teams"])

# Pydantic models for API responses
class TeamInfo(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    match_date: date
    match_time: Optional[time] = None
    week_number: Optional[int] = None
    home_team: TeamInfo
    away_team: TeamInfo
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    venue: Optional[str] = None
    attendance: Optional[int] = None
    referee: Optional[str] = None
    competition: str
    is_home_match: bool

    class Config:
        from_attributes = True

class TeamMatchesResponse(BaseModel):
    team_name: str
    matches: List[MatchResponse]
    total_matches_found: int

    class Config:
        from_attributes = True

@router.get("/{team_name}/matches", response_model=TeamMatchesResponse)
async def get_team_matches_endpoint(
    team_name: str,
    limit: int = Query(default=5, ge=1, le=20, description="Number of matches to return (1-20)")
):
    """
    Get the last N matches for a specific team.
    
    Args:
        team_name: Name of the team (case-insensitive, partial match supported)
        limit: Number of matches to return (default: 5, max: 20)
    
    Returns:
        TeamMatchesResponse with team info and their recent matches
    """
    session = get_db_session()
    
    try:
        team, matches = get_team_matches(session, team_name, limit)
        return format_team_matches_response(team, matches)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        session.close()

@router.get("/interesting_team_data")
async def get_interesting_team_data(
    team_name: str = Query(..., description="Team name (case-insensitive, partial match supported)")
):
    """
    Get team percentile values for each stat column in the squad standard table.
    
    Args:
        team_name: Name of the team (case-insensitive, partial match supported)
    
    Returns:
        Dictionary with stat column names as keys and percentile values as values
    """
    session = get_db_session()
    
    try:
        return get_team_rank(session, team_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        session.close()