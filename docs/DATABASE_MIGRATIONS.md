# Database Migration Guide

**Author:** Adrian Johnson <adrian207@gmail.com>

This guide provides comprehensive information on managing database migrations for the Mac OS Zero Trust Endpoint Security Platform using Alembic.

---

## Overview

The platform uses **Alembic** for database schema version control and migrations. This provides:

- **Schema Evolution:** Safely upgrade database schema across versions
- **Version Control:** Track all schema changes in code
- **Rollback Capability:** Downgrade to previous schema versions if needed
- **Automated Detection:** Auto-generate migrations from model changes
- **Multi-Environment Support:** Consistent migrations across dev, staging, production

---

## Quick Start

### Check Current Migration Status

```bash
python scripts/migrate.py current
```

### Apply All Pending Migrations

```bash
python scripts/migrate.py upgrade
```

### Check for Pending Migrations

```bash
python scripts/migrate.py check
```

---

## Migration Commands

### 1. Create a New Migration

**Auto-generate from model changes (recommended):**
```bash
python scripts/migrate.py create -m "Add user email index"
```

**Create empty migration for manual edits:**
```bash
python scripts/migrate.py create -m "Custom data migration" --no-autogenerate
```

**What happens:**
- Compares current database state with ORM models
- Generates migration script in `alembic/versions/`
- Creates `upgrade()` and `downgrade()` functions

**After creation:**
1. Review the generated migration file
2. Edit if necessary
3. Test in development environment
4. Commit to version control

---

### 2. Upgrade Database

**Upgrade to latest version:**
```bash
python scripts/migrate.py upgrade
```

**Upgrade by relative steps:**
```bash
python scripts/migrate.py upgrade --revision +1  # Upgrade one version
python scripts/migrate.py upgrade --revision +2  # Upgrade two versions
```

**Upgrade to specific revision:**
```bash
python scripts/migrate.py upgrade --revision abc123def
```

**Generate SQL without executing:**
```bash
python scripts/migrate.py upgrade --sql > migration.sql
```

---

### 3. Downgrade Database

**Downgrade one version:**
```bash
python scripts/migrate.py downgrade
```

**Downgrade to specific revision:**
```bash
python scripts/migrate.py downgrade --revision abc123def
```

**Downgrade to base (remove all migrations):**
```bash
python scripts/migrate.py downgrade --revision base
```

**Generate SQL without executing:**
```bash
python scripts/migrate.py downgrade --sql > rollback.sql
```

**⚠️ Warning:** Downgrade operations may result in data loss. Always backup before downgrading.

---

### 4. View Migration Information

**Show current revision:**
```bash
python scripts/migrate.py current
```

**Show migration history:**
```bash
python scripts/migrate.py history
```

**Show detailed history:**
```bash
python scripts/migrate.py history -v
```

**Show specific migration:**
```bash
python scripts/migrate.py show head
python scripts/migrate.py show abc123def
```

**Show current heads:**
```bash
python scripts/migrate.py heads
```

---

### 5. Stamp Database

Mark database as being at a specific revision without running migrations:

```bash
python scripts/migrate.py stamp --tag head
python scripts/migrate.py stamp --tag abc123def
```

**Use cases:**
- Initializing existing database
- Recovering from migration issues
- Synchronizing database state

---

## Migration Workflow

### Development Workflow

1. **Modify ORM Models**
   ```python
   # In telemetry/models.py
   class Device(BaseModel):
       # Add new field
       location = Column(String(255), nullable=True)
   ```

2. **Generate Migration**
   ```bash
   python scripts/migrate.py create -m "Add device location field"
   ```

3. **Review Generated Migration**
   ```bash
   cat alembic/versions/20251028_1200_add_device_location_field.py
   ```

4. **Test Migration**
   ```bash
   # Apply migration
   python scripts/migrate.py upgrade
   
   # Test application
   python main.py
   
   # Rollback if needed
   python scripts/migrate.py downgrade
   ```

5. **Commit to Version Control**
   ```bash
   git add alembic/versions/20251028_1200_add_device_location_field.py
   git commit -m "Add device location field"
   ```

---

### Production Deployment Workflow

1. **Backup Database**
   ```bash
   pg_dump -h localhost -U postgres mac_hardening > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Check Current State**
   ```bash
   python scripts/migrate.py current
   python scripts/migrate.py check
   ```

3. **Test Migration (Dry Run)**
   ```bash
   python scripts/migrate.py upgrade --sql > migration_preview.sql
   # Review SQL before executing
   ```

4. **Apply Migration**
   ```bash
   python scripts/migrate.py upgrade
   ```

5. **Verify Application**
   ```bash
   python main.py
   # Run health checks
   curl http://localhost:8000/health
   ```

6. **Rollback if Needed**
   ```bash
   python scripts/migrate.py downgrade
   # Restore from backup if necessary
   psql -h localhost -U postgres mac_hardening < backup_20251028_120000.sql
   ```

---

## Best Practices

### Creating Migrations

✅ **DO:**
- Create separate migrations for each logical change
- Use descriptive migration messages
- Review auto-generated migrations before committing
- Test migrations in development before production
- Include both `upgrade()` and `downgrade()` functions
- Add data migrations when changing column types

❌ **DON'T:**
- Modify existing migration files after deployment
- Create migrations for temporary development changes
- Skip testing migrations
- Deploy without reviewing migration SQL
- Mix schema changes with data migrations in complex cases

### Migration Messages

**Good examples:**
```bash
python scripts/migrate.py create -m "Add device location field"
python scripts/migrate.py create -m "Create index on security_events.event_time"
python scripts/migrate.py create -m "Rename user_email to email_address"
```

**Bad examples:**
```bash
python scripts/migrate.py create -m "Update"
python scripts/migrate.py create -m "Fix"
python scripts/migrate.py create -m "Changes"
```

### Data Migrations

For complex data transformations, create custom migrations:

```python
"""Migrate device status values

Revision ID: 20251028_1300
"""

def upgrade() -> None:
    # Update enum values
    op.execute("""
        UPDATE devices 
        SET enrollment_status = 'enrolled' 
        WHERE enrollment_status = 'active'
    """)

def downgrade() -> None:
    # Revert changes
    op.execute("""
        UPDATE devices 
        SET enrollment_status = 'active' 
        WHERE enrollment_status = 'enrolled'
    """)
```

---

## Troubleshooting

### Common Issues

#### Issue: "Can't locate revision identified by 'head'"

**Cause:** No migrations have been applied yet.

**Solution:**
```bash
# Check migration history
python scripts/migrate.py history

# Apply initial migration
python scripts/migrate.py upgrade --revision 20251028_0000
```

#### Issue: "Target database is not up to date"

**Cause:** Database schema doesn't match migration history.

**Solution:**
```bash
# Check current state
python scripts/migrate.py current

# Check what's pending
python scripts/migrate.py check

# Upgrade to latest
python scripts/migrate.py upgrade
```

#### Issue: "Migration failed with constraint violation"

**Cause:** Data doesn't meet new constraints (e.g., adding NOT NULL column with existing rows).

**Solution:**
1. Downgrade the migration
2. Modify migration to handle existing data
3. Re-run migration

Example fix:
```python
def upgrade() -> None:
    # Add column as nullable first
    op.add_column('devices', sa.Column('location', sa.String(255), nullable=True))
    
    # Set default value for existing rows
    op.execute("UPDATE devices SET location = 'Unknown' WHERE location IS NULL")
    
    # Make it non-nullable
    op.alter_column('devices', 'location', nullable=False)
```

#### Issue: "Downgrade removes data"

**Cause:** Downgrade operations may drop columns/tables.

**Solution:**
- Always backup before downgrading
- Consider keeping old columns temporarily
- Document data loss in migration comments

---

## Advanced Topics

### Branching and Merging

When multiple developers create migrations simultaneously:

```bash
# Identify branch points
python scripts/migrate.py heads

# Create merge migration
python scripts/migrate.py merge -m "Merge migration branches" <rev1> <rev2>
```

### Offline Migrations

Generate SQL for execution by DBAs:

```bash
# Generate upgrade SQL
python scripts/migrate.py upgrade --sql > upgrade.sql

# Generate downgrade SQL
python scripts/migrate.py downgrade --sql > downgrade.sql

# Execute manually
psql -h localhost -U postgres mac_hardening < upgrade.sql
```

### Custom Migration Templates

Modify `alembic/script.py.mako` to customize generated migrations:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Author: ${config.get_main_option("author", "Unknown")}
"""
```

### Testing Migrations

Create a test script:

```python
#!/usr/bin/env python3
"""Test migration up and down."""
import subprocess
import sys

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

# Apply migration
print("Applying migration...")
run_command("python scripts/migrate.py upgrade")

# Run tests
print("Running tests...")
run_command("pytest tests/test_database.py")

# Rollback
print("Rolling back...")
run_command("python scripts/migrate.py downgrade")

# Reapply
print("Reapplying migration...")
run_command("python scripts/migrate.py upgrade")

print("✅ Migration test passed!")
```

---

## Migration File Structure

### Directory Layout

```
alembic/
├── versions/
│   ├── 20251028_0000_initial_schema.py
│   ├── 20251029_1200_add_device_location.py
│   └── 20251030_0900_create_event_index.py
├── env.py           # Migration environment configuration
└── script.py.mako   # Migration template

alembic.ini          # Alembic configuration
scripts/
└── migrate.py       # Migration management script
```

### Migration File Format

```python
"""<description>

Revision ID: <unique_id>
Revises: <previous_revision>
Create Date: <timestamp>

Author: Adrian Johnson <adrian207@gmail.com>
"""
from alembic import op
import sqlalchemy as sa

revision = '<unique_id>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade database schema."""
    # Your upgrade logic here
    pass

def downgrade() -> None:
    """Downgrade database schema."""
    # Your downgrade logic here
    pass
```

---

## Integration with CI/CD

### Pre-deployment Check

```bash
#!/bin/bash
# check_migrations.sh

# Check if migrations are needed
python scripts/migrate.py check

if [ $? -ne 0 ]; then
    echo "⚠️  Database migrations required!"
    echo "Run: python scripts/migrate.py upgrade"
    exit 1
fi

echo "✅ Database is up to date"
```

### Automated Migration

```bash
#!/bin/bash
# deploy_with_migration.sh

set -e

echo "Backing up database..."
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

echo "Running migrations..."
python scripts/migrate.py upgrade

echo "Restarting application..."
docker-compose restart api

echo "Running health check..."
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed! Rolling back..."
    python scripts/migrate.py downgrade
    docker-compose restart api
    exit 1
}

echo "✅ Deployment successful!"
```

---

## FAQ

**Q: Can I modify an existing migration?**

A: No, once a migration is deployed, it should never be modified. Create a new migration instead.

**Q: What happens if I delete a migration file?**

A: Alembic will report errors. Never delete migration files that have been applied to any environment.

**Q: Can I skip migrations?**

A: No, migrations must be applied in order. Alembic tracks the migration chain.

**Q: How do I handle merge conflicts in migration files?**

A: Use `alembic merge` to create a merge migration that resolves both branches.

**Q: Can I run migrations on multiple databases simultaneously?**

A: Yes, but be careful with race conditions. Consider using database locks or coordinating deployments.

---

## Additional Resources

- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Platform Documentation:** `README.md`, `docs/DEPLOYMENT.md`
- **Database Models:** `telemetry/models.py`, `risk_engine/models.py`

---

## Support

For migration-related issues:

- **GitHub Issues:** [Mac-Compliance-System Issues](https://github.com/adrian207/Mac-Compliance-System/issues)
- **Email:** adrian207@gmail.com
- **Documentation:** See `docs/DEPLOYMENT.md` and `docs/OPERATIONS.md`

---

**Last Updated:** October 29, 2025  
**Version:** 0.9.2  
**Author:** Adrian Johnson <adrian207@gmail.com>

