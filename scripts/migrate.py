#!/usr/bin/env python3
"""
Database Migration Management Script

Author: Adrian Johnson <adrian207@gmail.com>

This script provides easy-to-use commands for managing database migrations
using Alembic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import click
from alembic import command
from alembic.config import Config

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


def get_alembic_config() -> Config:
    """
    Get Alembic configuration.
    
    Returns:
        Config: Alembic configuration object
    """
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    return alembic_cfg


@click.group()
def cli():
    """Database migration management commands."""
    pass


@cli.command()
@click.option(
    '--message', '-m',
    required=True,
    help='Migration message describing the changes'
)
@click.option(
    '--autogenerate/--no-autogenerate',
    default=True,
    help='Automatically detect schema changes'
)
def create(message: str, autogenerate: bool):
    """
    Create a new migration script.
    
    Examples:
        python scripts/migrate.py create -m "Add user email index"
        python scripts/migrate.py create -m "Initial schema" --no-autogenerate
    """
    try:
        alembic_cfg = get_alembic_config()
        
        if autogenerate:
            logger.info("generating_migration", message=message, autogenerate=True)
            command.revision(alembic_cfg, message=message, autogenerate=True)
            click.echo(f"✅ Created auto-generated migration: {message}")
        else:
            logger.info("creating_migration", message=message, autogenerate=False)
            command.revision(alembic_cfg, message=message)
            click.echo(f"✅ Created empty migration: {message}")
        
        click.echo("\n📝 Edit the migration file in alembic/versions/ before applying")
        
    except Exception as e:
        logger.error("migration_creation_failed", error=str(e))
        click.echo(f"❌ Error creating migration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--revision',
    default='head',
    help='Revision to upgrade to (default: head/latest)'
)
@click.option(
    '--sql',
    is_flag=True,
    help='Generate SQL instead of executing'
)
def upgrade(revision: str, sql: bool):
    """
    Upgrade database to a specific revision.
    
    Examples:
        python scripts/migrate.py upgrade
        python scripts/migrate.py upgrade --revision +1
        python scripts/migrate.py upgrade --sql
    """
    try:
        alembic_cfg = get_alembic_config()
        
        if sql:
            logger.info("generating_upgrade_sql", revision=revision)
            command.upgrade(alembic_cfg, revision, sql=True)
            click.echo(f"✅ Generated SQL for upgrade to {revision}")
        else:
            logger.info("upgrading_database", revision=revision)
            command.upgrade(alembic_cfg, revision)
            click.echo(f"✅ Database upgraded to {revision}")
        
    except Exception as e:
        logger.error("migration_upgrade_failed", error=str(e))
        click.echo(f"❌ Error upgrading database: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--revision',
    default='-1',
    help='Revision to downgrade to (default: -1/previous)'
)
@click.option(
    '--sql',
    is_flag=True,
    help='Generate SQL instead of executing'
)
def downgrade(revision: str, sql: bool):
    """
    Downgrade database to a specific revision.
    
    Examples:
        python scripts/migrate.py downgrade
        python scripts/migrate.py downgrade --revision base
        python scripts/migrate.py downgrade --sql
    """
    try:
        alembic_cfg = get_alembic_config()
        
        if sql:
            logger.info("generating_downgrade_sql", revision=revision)
            command.downgrade(alembic_cfg, revision, sql=True)
            click.echo(f"✅ Generated SQL for downgrade to {revision}")
        else:
            logger.info("downgrading_database", revision=revision)
            
            # Confirm downgrade
            if not click.confirm(f"⚠️  Are you sure you want to downgrade to {revision}?"):
                click.echo("Downgrade cancelled")
                return
            
            command.downgrade(alembic_cfg, revision)
            click.echo(f"✅ Database downgraded to {revision}")
        
    except Exception as e:
        logger.error("migration_downgrade_failed", error=str(e))
        click.echo(f"❌ Error downgrading database: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed migration information'
)
def current(verbose: bool):
    """
    Show current database revision.
    
    Examples:
        python scripts/migrate.py current
        python scripts/migrate.py current -v
    """
    try:
        alembic_cfg = get_alembic_config()
        
        if verbose:
            command.current(alembic_cfg, verbose=True)
        else:
            command.current(alembic_cfg)
        
    except Exception as e:
        logger.error("get_current_revision_failed", error=str(e))
        click.echo(f"❌ Error getting current revision: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed migration history'
)
def history(verbose: bool):
    """
    Show migration history.
    
    Examples:
        python scripts/migrate.py history
        python scripts/migrate.py history -v
    """
    try:
        alembic_cfg = get_alembic_config()
        
        if verbose:
            command.history(alembic_cfg, verbose=True)
        else:
            command.history(alembic_cfg)
        
    except Exception as e:
        logger.error("get_history_failed", error=str(e))
        click.echo(f"❌ Error getting history: {e}", err=True)
        sys.exit(1)


@cli.command()
def heads():
    """
    Show current available heads in the migration tree.
    
    Examples:
        python scripts/migrate.py heads
    """
    try:
        alembic_cfg = get_alembic_config()
        command.heads(alembic_cfg)
        
    except Exception as e:
        logger.error("get_heads_failed", error=str(e))
        click.echo(f"❌ Error getting heads: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('revision')
def show(revision: str):
    """
    Show details of a specific migration.
    
    Examples:
        python scripts/migrate.py show head
        python scripts/migrate.py show abc123
    """
    try:
        alembic_cfg = get_alembic_config()
        command.show(alembic_cfg, revision)
        
    except Exception as e:
        logger.error("show_migration_failed", error=str(e))
        click.echo(f"❌ Error showing migration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--tag',
    help='Arbitrary "tag" name for the migration'
)
@click.option(
    '--sql',
    is_flag=True,
    help='Generate SQL instead of executing'
)
def stamp(tag: str, sql: bool):
    """
    'Stamp' the revision table with the given revision without running migrations.
    
    [Inference] This is useful when you need to set the database to a specific
    revision state without actually running the migrations.
    
    Examples:
        python scripts/migrate.py stamp head
        python scripts/migrate.py stamp abc123
    """
    try:
        if not tag:
            click.echo("❌ Error: --tag is required", err=True)
            sys.exit(1)
        
        alembic_cfg = get_alembic_config()
        
        if sql:
            command.stamp(alembic_cfg, tag, sql=True)
            click.echo(f"✅ Generated SQL for stamping to {tag}")
        else:
            logger.info("stamping_database", tag=tag)
            
            if not click.confirm(f"⚠️  Stamp database to {tag}?"):
                click.echo("Stamp cancelled")
                return
            
            command.stamp(alembic_cfg, tag)
            click.echo(f"✅ Database stamped to {tag}")
        
    except Exception as e:
        logger.error("stamp_failed", error=str(e))
        click.echo(f"❌ Error stamping database: {e}", err=True)
        sys.exit(1)


@cli.command()
def check():
    """
    Check if there are any pending migrations.
    
    Examples:
        python scripts/migrate.py check
    """
    try:
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        # Get application config
        app_config = get_config()
        
        # Create engine
        engine = create_engine(app_config.database.connection_string)
        
        # Get current revision from database
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
        
        # Get head revision from scripts
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        
        if current_rev == head_rev:
            click.echo(f"✅ Database is up to date (revision: {current_rev})")
        else:
            click.echo(f"⚠️  Database needs migration")
            click.echo(f"   Current: {current_rev or 'base'}")
            click.echo(f"   Latest:  {head_rev}")
            click.echo(f"\nRun: python scripts/migrate.py upgrade")
            sys.exit(1)
        
    except Exception as e:
        logger.error("check_failed", error=str(e))
        click.echo(f"❌ Error checking migrations: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

