"""
Configuration Tests

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config, get_config


def test_load_example_config():
    """Test loading example configuration."""
    config = load_config("config/config.example.yaml")
    
    assert config is not None
    assert config.platform_name == "Mac OS Zero Trust Security Platform"
    assert config.platform_version == "1.0.0"


def test_config_has_required_sections():
    """Test that config has all required sections."""
    config = get_config()
    
    # Check main sections exist
    assert hasattr(config, 'database')
    assert hasattr(config, 'api')
    assert hasattr(config, 'risk_assessment')
    assert hasattr(config, 'hardening')


def test_risk_assessment_config():
    """Test risk assessment configuration."""
    config = get_config()
    
    # Check weights sum to 100
    weights = config.risk_assessment.weights
    total = (weights.security_posture + weights.compliance + 
             weights.behavioral + weights.threat_indicators)
    
    assert total == 100, f"Risk weights must sum to 100, got {total}"
    
    # Check thresholds are in order
    thresholds = config.risk_assessment.thresholds
    assert thresholds.low < thresholds.medium
    assert thresholds.medium < thresholds.high
    assert thresholds.high < thresholds.critical


def test_hardening_config():
    """Test hardening configuration."""
    config = get_config()
    
    assert config.hardening.minimum_os_version is not None
    assert config.hardening.require_filevault is not None
    assert config.hardening.require_firewall is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

