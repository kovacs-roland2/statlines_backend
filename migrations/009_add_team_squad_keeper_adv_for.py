"""Migration to add team_squad_keeper_adv_for table."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

DESCRIPTION = "Add team_squad_keeper_adv_for table for storing advanced team squad keeper statistics including season and competition data."

def run_migration() -> None:
    session = get_db_session()
    try:
        print("Starting migration: Add team_squad_keeper_adv_for table...")
        session.execute(text("""
            CREATE TABLE team_squad_keeper_adv_for (
                id SERIAL PRIMARY KEY,
                competition_id INTEGER NOT NULL REFERENCES competitions(id),
                team_id INTEGER NOT NULL REFERENCES teams(id),
                season VARCHAR(20) NOT NULL,
                free_kick_goals_against INTEGER,
                corner_kick_goals_against INTEGER,
                own_goals_against INTEGER,
                post_shot_xg FLOAT,
                post_shot_xg_per_shot_ot FLOAT,
                post_shot_xg_minus_goals_allowed FLOAT,
                post_shot_xg_minus_goals_allowed_90s FLOAT,
                completed_long_balls INTEGER,
                attempted_long_balls INTEGER,
                long_balls_completed_percentage FLOAT,
                passes_attempted INTEGER,
                throws_attempted INTEGER,
                launch_percentage FLOAT,
                avg_pass_length FLOAT,
                goal_kicks INTEGER,
                goal_kicks_launched_percentage FLOAT,
                goal_kicks_avg_length FLOAT,
                crosses_faced INTEGER,
                crosses_stopped INTEGER,
                crosses_stopped_percentage FLOAT,
                def_actions_outside_of_penalty_area INTEGER,
                def_actions_outside_of_penalty_area_90s FLOAT,
                avg_def_action_dist FLOAT,
                scraped_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """))
        session.commit()
        print("Table created.")

        print("Adding indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_adv_for_competition ON team_squad_keeper_adv_for(competition_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_adv_for_team ON team_squad_keeper_adv_for(team_id)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_adv_for_season ON team_squad_keeper_adv_for(season)",
            "CREATE INDEX IF NOT EXISTS idx_team_squad_keeper_adv_for_unique ON team_squad_keeper_adv_for(team_id, season, competition_id)"
        ]
        for index_sql in indexes:
            try:
                session.execute(text(index_sql))
                session.commit()
            except Exception as e:
                session.rollback()
                if "already exists" in str(e).lower():
                    print(f"Index already exists: {index_sql}")
                else:
                    raise e

        print("Adding unique constraint...")
        try:
            session.execute(text("""
                ALTER TABLE team_squad_keeper_adv_for
                ADD CONSTRAINT uk_team_squad_standard_keeper_against
                UNIQUE (team_id, season, competition_id)
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Unique constraint already exists")
            else:
                raise e

        print("Adding updated_at trigger...")
        try:
            session.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """))
            session.execute(text("""
                CREATE TRIGGER update_team_squad_keeper_adv_for_updated_at 
                BEFORE UPDATE ON team_squad_keeper_adv_for
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            if "already exists" in str(e).lower():
                print("Trigger already exists")
            else:
                print(f"Warning: Could not create trigger: {e}")

        print("Verifying migration...")
        table_exists = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'team_squad_keeper_adv_for'
            )
        """)).scalar()
        if table_exists:
            print("team_squad_keeper_adv_for table created successfully!")
        else:
            raise Exception("team_squad_keeper_adv_for table was not created")
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration() 