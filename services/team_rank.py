from fastapi import HTTPException
from sqlalchemy import or_, desc
from database.models import Team, TeamSquadStandardFor

def get_team_rank(session, team_name: str, stat_columns=None):
    """
    Returns the team's top 5 highest and lowest ranked stats in TeamSquadStandardFor.
    
    Returns:
        Dictionary with 'top_5_highest' and 'top_5_lowest' containing stat rankings
    """
    if stat_columns is None:
        stat_columns = [
            "player_number", "age", "possession", "goals", "assists",
            "goals_minus_penalties", "penalties", "penalties_attempted", "yellow_cards", "red_cards",
            "expected_goals", "non_penalty_expected_goals", "expected_assisted_goals", "npxg_plus_xag",
            "progressive_carries", "progressive_passes", "goals_per90", "assists_per90",
            "goals_and_assists_per90", "goals_minus_penalties_per90", "goals_and_assists_minus_penalties_per90",
            "expected_goals_per90", "expected_assisted_goals_per90", "expected_goals_and_assists_per90",
            "non_penalty_expected_goals_per90", "npxg_plus_xag_per90"
        ]

    # Find the team
    team = session.query(Team).filter(
        or_(
            Team.name.ilike(f"%{team_name}%"),
            Team.short_name.ilike(f"%{team_name}%")
        )
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found.")

    # Get the latest season for this team in TeamSquadStandardFor
    team_row = session.query(TeamSquadStandardFor).filter(
        TeamSquadStandardFor.team_id == team.id
    ).order_by(desc(TeamSquadStandardFor.season)).first()
    if not team_row:
        return {"top_5_highest": [], "top_5_lowest": []}

    # Get the latest season overall (for all teams)
    latest_season = session.query(TeamSquadStandardFor.season).order_by(desc(TeamSquadStandardFor.season)).first()
    if not latest_season:
        return {"top_5_highest": [], "top_5_lowest": []}

    latest_season = latest_season[0]

    # Get all rows for the latest season
    all_rows = session.query(TeamSquadStandardFor).filter(
        TeamSquadStandardFor.season == latest_season
    ).all()
    if not all_rows:
        return {"top_5_highest": [], "top_5_lowest": []}

    stat_rankings = []

    for col in stat_columns:
        # Get all values for this stat in the latest season
        all_values = [getattr(row, col) for row in all_rows if getattr(row, col) is not None]
        if not all_values:
            continue

        team_value = getattr(team_row, col)
        if team_value is None:
            continue

        # Calculate rank (1 = best, higher rank = worse)
        rank = sum(1 for x in all_values if x > team_value) + 1
        total_teams = len(all_values)
        
        stat_rankings.append({
            "stat": col,
            "value": float(team_value),
            "rank": rank,
            "total": total_teams
        })

    # Sort by rank (best first)
    stat_rankings.sort(key=lambda x: x["rank"])

    top_5_highest = stat_rankings[:5]
    top_5_lowest = stat_rankings[-5:][::-1]  # Reverse to show worst first

    return {
        "team_name": team.name,
        "season": latest_season,
        "top_5_highest": top_5_highest,
        "top_5_lowest": top_5_lowest
    }
