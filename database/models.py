from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Text
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Migration(Base):
    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text)

    def __repr__(self):
        return f"<Migration(name='{self.name}', applied_at={self.applied_at})>"

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    short_name = Column(String(20))
    country = Column(String(50))
    fbref_id = Column(Integer, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    matches = relationship("Match", back_populates="competition")
    teams = relationship("Team", back_populates="competition")

    def __repr__(self):
        return f"<Competition(id={self.id}, name='{self.name}', fbref_id={self.fbref_id})>"

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    short_name = Column(String(20))
    competition_id = Column(Integer, ForeignKey("competitions.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition", back_populates="teams")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', short_name='{self.short_name}')>"

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), index=True)
    week_number = Column(Integer)
    match_date = Column(Date, nullable=False, index=True)
    match_time = Column(Time)
    home_team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    away_team_id = Column(Integer, ForeignKey("teams.id"), index=True)
    home_score = Column(Integer)
    away_score = Column(Integer)
    home_xg = Column(Numeric(4, 2))
    away_xg = Column(Numeric(4, 2))
    venue = Column(String(100))
    attendance = Column(Integer)
    referee = Column(String(100))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

    def __repr__(self):
        return f"<Match(id={self.id}, date={self.match_date}, home_team_id={self.home_team_id}, away_team_id={self.away_team_id})>"

class TeamOverallTableResults(Base):
    __tablename__ = "team_overall_table_results"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(String(20), nullable=False, index=True)  # e.g., "2023-24"
    rk = Column(Integer)  # Rank
    squad = Column(String(100), nullable=False)  # Team name as it appears in the table
    mp = Column(Integer)  # Matches played
    w = Column(Integer)   # Wins
    d = Column(Integer)   # Draws
    l = Column(Integer)   # Losses
    gf = Column(Integer)  # Goals for
    ga = Column(Integer)  # Goals against
    gd = Column(Integer)  # Goal difference
    pts = Column(Integer) # Points
    pts_per_mp = Column(Numeric(4, 2))  # Points per match played
    xg = Column(Numeric(5, 2))   # Expected goals
    xga = Column(Numeric(5, 2))  # Expected goals against
    xgd = Column(Numeric(5, 2))  # Expected goal difference
    xgd_per_90 = Column(Numeric(4, 3))  # Expected goal difference per 90 minutes
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    competition = relationship("Competition")
    team = relationship("Team")

    def __repr__(self):
        return f"<TeamOverallTableResults(id={self.id}, squad='{self.squad}', season='{self.season}', rk={self.rk})>"

    class Config:
        from_attributes = True

class TeamHomeAwayTableResults(Base):
    __tablename__ = "team_home_away_table_results"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    season = Column(String(20), nullable=False, index=True)

    # Home columns
    home_mp = Column(Integer)
    home_w = Column(Integer)
    home_d = Column(Integer)
    home_l = Column(Integer)
    home_gf = Column(Integer)
    home_ga = Column(Integer)
    home_gd = Column(Integer)
    home_pts = Column(Integer)
    home_pts_per_mp = Column(Numeric(4, 2))
    home_xg = Column(Numeric(5, 2))
    home_xga = Column(Numeric(5, 2))
    home_xgd = Column(Numeric(5, 2))
    home_xgd_per_90 = Column(Numeric(4, 3))

    # Away columns
    away_mp = Column(Integer)
    away_w = Column(Integer)
    away_d = Column(Integer)
    away_l = Column(Integer)
    away_gf = Column(Integer)
    away_ga = Column(Integer)
    away_gd = Column(Integer)
    away_pts = Column(Integer)
    away_pts_per_mp = Column(Numeric(4, 2))
    away_xg = Column(Numeric(5, 2))
    away_xga = Column(Numeric(5, 2))
    away_xgd = Column(Numeric(5, 2))
    away_xgd_per_90 = Column(Numeric(4, 3))

    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    competition = relationship("Competition")
    team = relationship("Team")

    def __repr__(self):
        return f"<TeamHomeAwayTableResults(id={self.id}, team_id={self.team_id}, season='{self.season}')>"

    class Config:
        from_attributes = True