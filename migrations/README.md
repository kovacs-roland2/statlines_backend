# Database Migrations

This directory contains database migration scripts for the StatLines backend.

## Migration System

The migration system tracks which database changes have been applied and prevents duplicate runs.

### Commands

```bash
# Check migration status
python migrations/migration_runner.py status

# Run all pending migrations
python migrations/migration_runner.py run-all

# Run a specific migration
python migrations/migration_runner.py run --migration 001_add_competitions
```

### Creating New Migrations

1. **Naming Convention**: Use format `XXX_description.py` where XXX is a 3-digit number
2. **Required Function**: Each migration must have a `run_migration()` function
3. **Description**: Add a `DESCRIPTION` constant for documentation

Example migration structure:
```python
#!/usr/bin/env python3
"""
Migration: Description of what this migration does
"""

# Migration metadata
DESCRIPTION = "Brief description of the migration"

def run_migration():
    """Implement the migration logic here."""
    # Your migration code
    pass
```

### Migration History

- `001_add_competitions.py` - Add competitions table and competition_id to matches for multi-league support

### Best Practices

1. **Keep migrations** - Never delete migration files
2. **Test migrations** - Always test on development database first
3. **Backup data** - Create backups before running migrations in production
4. **Rollback plan** - Consider how to reverse changes if needed
5. **Small changes** - Keep migrations focused and atomic 