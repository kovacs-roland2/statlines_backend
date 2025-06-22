#!/usr/bin/env python3
"""
Migration runner system for database schema changes.
"""

import sys
import os
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import get_db_session
from sqlalchemy import text

class MigrationRunner:
    def __init__(self):
        self.session = get_db_session()
        self.migrations_dir = Path(__file__).parent
        self.ensure_migrations_table()
    
    def ensure_migrations_table(self):
        """Ensure the migrations table exists."""
        try:
            self.session.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            self.session.commit()
        except Exception as e:
            print(f"Error creating migrations table: {e}")
            self.session.rollback()
    
    def get_applied_migrations(self):
        """Get list of already applied migrations."""
        try:
            result = self.session.execute(text("SELECT name FROM migrations ORDER BY applied_at"))
            return [row[0] for row in result]
        except Exception:
            return []
    
    def get_pending_migrations(self):
        """Get list of migrations that haven't been applied yet."""
        applied = set(self.get_applied_migrations())
        
        # Find all migration files
        migration_files = []
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name != "__init__.py" and file_path.name != "migration_runner.py":
                migration_files.append(file_path.stem)
        
        # Return migrations that haven't been applied
        pending = [name for name in sorted(migration_files) if name not in applied]
        return pending
    
    def run_migration(self, migration_name):
        """Run a specific migration."""
        migration_file = self.migrations_dir / f"{migration_name}.py"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Load the migration module
        spec = importlib.util.spec_from_file_location(migration_name, migration_file)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # Run the migration
        print(f"Running migration: {migration_name}")
        
        if hasattr(migration_module, 'run_migration'):
            migration_module.run_migration()
        elif hasattr(migration_module, 'main'):
            migration_module.main()
        else:
            raise AttributeError(f"Migration {migration_name} must have 'run_migration' or 'main' function")
        
        # Record the migration as applied
        description = getattr(migration_module, 'DESCRIPTION', None)
        self.record_migration(migration_name, description)
        
        print(f"Migration {migration_name} completed successfully")
    
    def record_migration(self, migration_name, description=None):
        """Record a migration as applied."""
        try:
            self.session.execute(text("""
                INSERT INTO migrations (name, description) 
                VALUES (:name, :description)
                ON CONFLICT (name) DO NOTHING
            """), {
                'name': migration_name,
                'description': description
            })
            self.session.commit()
        except Exception as e:
            print(f"Error recording migration: {e}")
            self.session.rollback()
    
    def run_pending_migrations(self):
        """Run all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("No pending migrations")
            return
        
        print(f"Found {len(pending)} pending migrations:")
        for migration in pending:
            print(f"  - {migration}")
        
        for migration in pending:
            try:
                self.run_migration(migration)
            except Exception as e:
                print(f"Migration {migration} failed: {e}")
                break
        
        print("All pending migrations completed")
    
    def show_migration_status(self):
        """Show status of all migrations."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("Migration Status:")
        print("=" * 50)
        
        if applied:
            print("Applied migrations:")
            for migration in applied:
                print(f"  - {migration}")
        
        if pending:
            print("\nPending migrations:")
            for migration in pending:
                print(f"  - {migration}")
        
        if not applied and not pending:
            print("No migrations found")
    
    def close(self):
        """Close database session."""
        self.session.close()

def main():
    """CLI interface for migration runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('command', choices=['status', 'run', 'run-all'], 
                       help='Command to execute')
    parser.add_argument('--migration', help='Specific migration to run')
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    
    try:
        if args.command == 'status':
            runner.show_migration_status()
        elif args.command == 'run':
            if not args.migration:
                print("Error: --migration required for 'run' command")
                return
            runner.run_migration(args.migration)
        elif args.command == 'run-all':
            runner.run_pending_migrations()
    finally:
        runner.close()

if __name__ == "__main__":
    main() 