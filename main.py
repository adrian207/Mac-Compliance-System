"""
Mac OS Zero Trust Endpoint Security Platform - Main Application

Author: Adrian Johnson <adrian207@gmail.com>

Main entry point for the Zero Trust security platform.
"""

import sys
import time
from datetime import datetime

from core.config import get_config
from core.database import get_db_manager
from core.logging_config import setup_logging, get_logger

logger = None


def initialize_platform():
    """Initialize the platform components."""
    global logger
    
    print("=" * 70)
    print("Mac OS Zero Trust Endpoint Security Platform")
    print("Author: Adrian Johnson <adrian207@gmail.com>")
    print("=" * 70)
    print()
    
    # Load configuration
    print("Loading configuration...")
    try:
        config = get_config()
        print(f"✓ Configuration loaded (environment: {config.environment})")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False
    
    # Setup logging
    print("Setting up logging...")
    try:
        setup_logging(
            log_level=config.log_level,
            log_file="logs/platform.log",
            json_format=True
        )
        logger = get_logger(__name__)
        print(f"✓ Logging configured (level: {config.log_level})")
    except Exception as e:
        print(f"✗ Failed to setup logging: {e}")
        return False
    
    # Initialize database
    print("Initializing database...")
    try:
        db_manager = get_db_manager()
        db_manager.create_tables()
        print(f"✓ Database initialized ({config.database.type})")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        logger.error("database_initialization_failed", error=str(e))
        return False
    
    # Test integrations
    print("Testing integrations...")
    integration_status = []
    
    # Test Kandji
    if config.kandji and config.kandji.enabled:
        try:
            from integrations.kandji import get_kandji_client
            with get_kandji_client() as kandji:
                if kandji.test_connection():
                    integration_status.append(("Kandji", "✓ Connected"))
                else:
                    integration_status.append(("Kandji", "✗ Connection failed"))
        except Exception as e:
            integration_status.append(("Kandji", f"✗ Error: {str(e)[:50]}"))
    else:
        integration_status.append(("Kandji", "⊘ Disabled"))
    
    # Test Zscaler
    if config.zscaler and config.zscaler.enabled:
        try:
            from integrations.zscaler import get_zscaler_client
            with get_zscaler_client() as zscaler:
                if zscaler.test_connection():
                    integration_status.append(("Zscaler", "✓ Connected"))
                else:
                    integration_status.append(("Zscaler", "✗ Connection failed"))
        except Exception as e:
            integration_status.append(("Zscaler", f"✗ Error: {str(e)[:50]}"))
    else:
        integration_status.append(("Zscaler", "⊘ Disabled"))
    
    # Test Seraphic
    if config.seraphic and config.seraphic.enabled:
        try:
            from integrations.seraphic import get_seraphic_client
            with get_seraphic_client() as seraphic:
                if seraphic.test_connection():
                    integration_status.append(("Seraphic", "✓ Connected"))
                else:
                    integration_status.append(("Seraphic", "✗ Connection failed"))
        except Exception as e:
            integration_status.append(("Seraphic", f"✗ Error: {str(e)[:50]}"))
    else:
        integration_status.append(("Seraphic", "⊘ Disabled"))
    
    for integration, status in integration_status:
        print(f"  {integration:12} {status}")
    
    print()
    logger.info("platform_initialized", integrations=integration_status)
    
    return True


def run_platform():
    """Run the main platform loop."""
    logger.info("platform_started")
    
    print("Platform initialized successfully!")
    print()
    print("Services available:")
    print("  - API Server: http://localhost:8000")
    print("  - Metrics: http://localhost:9090/metrics")
    print("  - Dashboard: http://localhost:8000/dashboard")
    print()
    print("Press Ctrl+C to stop the platform")
    print()
    
    try:
        # Keep platform running
        while True:
            time.sleep(60)
            
            # Periodic health check
            logger.debug("platform_health_check")
    
    except KeyboardInterrupt:
        print("\n\nShutting down platform...")
        logger.info("platform_shutdown_requested")
        
        # Cleanup
        try:
            db_manager = get_db_manager()
            db_manager.close()
            print("✓ Database connections closed")
        except Exception as e:
            print(f"✗ Error during cleanup: {e}")
        
        print("Platform stopped")
        logger.info("platform_stopped")


def main():
    """Main entry point."""
    if not initialize_platform():
        print("\nPlatform initialization failed. Exiting.")
        sys.exit(1)
    
    run_platform()


if __name__ == "__main__":
    main()

