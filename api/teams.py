from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, time
import sys
import os

# Add the parent directory to the path so we can import from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from database.models import Match, Team
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, desc

# Create router for team-related endpoints
router = APIRouter(prefix="/api/teams", tags=["teams"])

# Pydantic models for API responses
class TeamInfo(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None

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

class TeamMatchesResponse(BaseModel):
    team_name: str
    matches: List[MatchResponse]
    total_matches_found: int

@router.get("/{team_name}/matches", response_model=TeamMatchesResponse)
async def get_team_matches(
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
        
        # Format the response
        match_responses = []
        for match in matches:
            is_home_match = match.home_team_id == team.id
            
            match_response = MatchResponse(
                id=match.id,
                match_date=match.match_date,
                match_time=match.match_time,
                week_number=match.week_number,
                home_team=TeamInfo(
                    id=match.home_team.id,
                    name=match.home_team.name,
                    short_name=match.home_team.short_name
                ),
                away_team=TeamInfo(
                    id=match.away_team.id,
                    name=match.away_team.name,
                    short_name=match.away_team.short_name
                ),
                home_score=match.home_score,
                away_score=match.away_score,
                home_xg=float(match.home_xg) if match.home_xg else None,
                away_xg=float(match.away_xg) if match.away_xg else None,
                venue=match.venue,
                attendance=match.attendance,
                referee=match.referee,
                competition=match.competition.name if match.competition else "Unknown",
                is_home_match=is_home_match
            )
            match_responses.append(match_response)
        
        return TeamMatchesResponse(
            team_name=team.name,
            matches=match_responses,
            total_matches_found=len(match_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        session.close() 