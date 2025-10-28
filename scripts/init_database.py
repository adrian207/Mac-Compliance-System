#!/usr/bin/env python3
"""
Database Initialization Script

Author: Adrian Johnson <adrian207@gmail.com>

Initializes the database schema for the Zero Trust platform.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.database import get_db_manager
from core.logging_config import setup_logging, get_logger

# Import all models to ensure they're registered
from telemetry.models import (
    Device, TelemetrySnapshot, SecurityEvent, ComplianceResult,
    NetworkConnection, SoftwareInventory
)
from risk_engine.models import RiskScore, RiskFactor, RiskTrend
from workflows.models import WorkflowExecution, WorkflowAction, WorkflowSchedule, IncidentTicket


def main():
    """Initialize database."""
    print("=" * 70)
    print("Database Initialization")
    print("Author: Adrian Johnson <adrian207@gmail.com>")
    print("=" * 70)
    print()
    
    # Load configuration
    print("Loading configuration...")
    try:
        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"  Database: {config.database.type}")
        print(f"  Host: {config.database.host}")
        print(f"  Database: {config.database.database}")
        print()
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    # Setup logging
    setup_logging(log_level=config.log_level)
    logger = get_logger(__name__)
    
    # Initialize database
    print("Initializing database connection...")
    try:
        db_manager = get_db_manager()
        print("✓ Database connection established")
        print()
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        logger.error("database_connection_failed", error=str(e))
        return 1
    
    # Create tables
    print("Creating database tables...")
    try:
        db_manager.create_tables()
        print("✓ Database tables created successfully")
        print()
        
        print("Tables created:")
        print("  - devices")
        print("  - telemetry_snapshots")
        print("  - security_events")
        print("  - compliance_results")
        print("  - network_connections")
        print("  - software_inventory")
        print("  - risk_scores")
        print("  - risk_factors")
        print("  - risk_trends")
        print("  - workflow_executions")
        print("  - workflow_actions")
        print("  - workflow_schedules")
        print("  - incident_tickets")
        print()
        
        logger.info("database_initialized")
        
    except Exception as e:
        print(f"✗ Failed to create tables: {e}")
        logger.error("database_creation_failed", error=str(e))
        return 1
    
    print("Database initialization complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

