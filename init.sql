-- Create teams table first (referenced by matches)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    short_name VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create matches table
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    week_number INTEGER,
    match_date DATE NOT NULL,
    match_time TIME,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    home_xg DECIMAL(4,2),
    away_xg DECIMAL(4,2),
    venue VARCHAR(100),
    attendance INTEGER,
    referee VARCHAR(100),
    match_report_url TEXT,
    notes TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);

-- Insert some initial Premier League teams
INSERT INTO teams (name, short_name) VALUES 
('Arsenal', 'ARS'),
('Aston Villa', 'AVL'),
('Brighton & Hove Albion', 'BHA'),
('Burnley', 'BUR'),
('Chelsea', 'CHE'),
('Crystal Palace', 'CRY'),
('Everton', 'EVE'),
('Fulham', 'FUL'),
('Liverpool', 'LIV'),
('Luton Town', 'LUT'),
('Manchester City', 'MCI'),
('Manchester United', 'MUN'),
('Newcastle United', 'NEW'),
('Nottingham Forest', 'NFO'),
('Sheffield United', 'SHU'),
('Tottenham Hotspur', 'TOT'),
('West Ham United', 'WHU'),
('Wolverhampton Wanderers', 'WOL'),
('Brentford', 'BRE'),
('Bournemouth', 'BOU')
ON CONFLICT (name) DO NOTHING; 