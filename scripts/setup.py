#!/usr/bin/env python3
"""
Platform Setup Script

Author: Adrian Johnson <adrian207@gmail.com>

Performs initial setup of the Zero Trust platform.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.logging_config import setup_logging, get_logger


def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "data",
        "reports",
        "exports"
    ]
    
    print("Creating directories...")
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"  ✓ {directory}/")
    print()


def verify_configuration():
    """Verify configuration is valid."""
    print("Verifying configuration...")
    try:
        config = get_config()
        
        issues = []
        
        # Check database config
        if not config.database:
            issues.append("Database configuration is missing")
        
        # Check integration configs
        enabled_integrations = []
        if config.kandji and config.kandji.enabled:
            enabled_integrations.append("Kandji")
        if config.zscaler and config.zscaler.enabled:
            enabled_integrations.append("Zscaler")
        if config.seraphic and config.seraphic.enabled:
            enabled_integrations.append("Seraphic")
        
        if not enabled_integrations:
            issues.append("No integrations are enabled")
        
        if issues:
            print("  ✗ Configuration issues found:")
            for issue in issues:
                print(f"    - {issue}")
            return False
        else:
            print("  ✓ Configuration is valid")
            print(f"  Enabled integrations: {', '.join(enabled_integrations)}")
            return True
    
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False
    
    print()


def test_integrations():
    """Test integration connections."""
    print("Testing integration connections...")
    config = get_config()
    
    # Test Kandji
    if config.kandji and config.kandji.enabled:
        try:
            from integrations.kandji import get_kandji_client
            with get_kandji_client() as kandji:
                if kandji.test_connection():
                    print("  ✓ Kandji connection successful")
                else:
                    print("  ✗ Kandji connection failed")
        except Exception as e:
            print(f"  ✗ Kandji error: {str(e)[:60]}")
    
    # Test Zscaler
    if config.zscaler and config.zscaler.enabled:
        try:
            from integrations.zscaler import get_zscaler_client
            with get_zscaler_client() as zscaler:
                if zscaler.test_connection():
                    print("  ✓ Zscaler connection successful")
                else:
                    print("  ✗ Zscaler connection failed")
        except Exception as e:
            print(f"  ✗ Zscaler error: {str(e)[:60]}")
    
    # Test Seraphic
    if config.seraphic and config.seraphic.enabled:
        try:
            from integrations.seraphic import get_seraphic_client
            with get_seraphic_client() as seraphic:
                if seraphic.test_connection():
                    print("  ✓ Seraphic connection successful")
                else:
                    print("  ✗ Seraphic connection failed")
        except Exception as e:
            print(f"  ✗ Seraphic error: {str(e)[:60]}")
    
    print()


def main():
    """Run setup."""
    print("=" * 70)
    print("Mac OS Zero Trust Platform Setup")
    print("Author: Adrian Johnson <adrian207@gmail.com>")
    print("=" * 70)
    print()
    
    # Create directories
    create_directories()
    
    # Verify configuration
    if not verify_configuration():
        print("\n⚠  Please fix configuration issues in config/config.yaml")
        print()
        return 1
    
    # Test integrations
    test_integrations()
    
    print("=" * 70)
    print("Setup complete!")
    print()
    print("Next steps:")
    print("  1. Initialize the database:")
    print("     python scripts/init_database.py")
    print()
    print("  2. Start the platform:")
    print("     python main.py")
    print()
    print("  3. Start the API server (in another terminal):")
    print("     python api_server.py")
    print("=" * 70)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

