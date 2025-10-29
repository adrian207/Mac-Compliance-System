"""
Alembic Migration Environment

Author: Adrian Johnson <adrian207@gmail.com>

This module configures the Alembic migration environment and connects it
to the application's database configuration and models.
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import application components
from core.config import get_config
from core.database import Base

# Import all models to ensure they're registered with Base.metadata
from telemetry.models import (
    Device, TelemetrySnapshot, SecurityEvent, ComplianceResult,
    NetworkConnection, SoftwareInventory
)
from risk_engine.models import RiskScore, RiskFactor, RiskTrend

# Import workflow models if they exist
try:
    from workflows.models import WorkflowExecution, WorkflowAction
except ImportError:
    pass

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from application configuration.
    
    Returns:
        str: Database connection string
    """
    app_config = get_config()
    return app_config.database.connection_string


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() will emit the given string to the script output.
    
    [Inference] This mode is useful for generating SQL scripts without
    connecting to the database.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    This mode connects to the database and executes migrations directly.
    """
    # Get database URL from application config
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Needed for SQLite compatibility
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

