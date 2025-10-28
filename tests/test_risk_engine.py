"""
Risk Engine Tests

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_engine.assessor import RiskAssessor


# Mock telemetry data
SECURE_TELEMETRY = {
    "system_info": {
        "hostname": "test-mac",
        "os_version": "14.0",
        "uuid": "test-uuid-123"
    },
    "security_status": {
        "filevault_enabled": True,
        "firewall_enabled": True,
        "gatekeeper_enabled": True,
        "sip_enabled": True
    },
    "authentication": {
        "password_required": True,
        "screen_lock_enabled": True
    },
    "network_info": {
        "ip_address": "192.168.1.100",
        "wifi_ssid": "TestNetwork"
    },
    "processes": [],
    "network_connections": []
}

INSECURE_TELEMETRY = {
    "system_info": {
        "hostname": "test-mac",
        "os_version": "11.0",  # Outdated
        "uuid": "test-uuid-456"
    },
    "security_status": {
        "filevault_enabled": False,  # Critical issue
        "firewall_enabled": False,   # High issue
        "gatekeeper_enabled": False, # High issue
        "sip_enabled": False         # Critical issue
    },
    "authentication": {
        "password_required": False,   # Critical issue
        "screen_lock_enabled": False
    },
    "network_info": {
        "ip_address": "192.168.1.101"
    },
    "processes": [],
    "network_connections": []
}


def test_risk_assessor_initialization():
    """Test risk assessor initializes correctly."""
    assessor = RiskAssessor()
    
    assert assessor is not None
    assert assessor.weights is not None
    assert assessor.thresholds is not None


def test_secure_device_low_risk():
    """Test that a secure device gets low risk score."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(SECURE_TELEMETRY)
    
    assert assessment["total_risk_score"] < 30
    assert assessment["risk_level"] in ["low"]


def test_insecure_device_high_risk():
    """Test that an insecure device gets high risk score."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(INSECURE_TELEMETRY)
    
    assert assessment["total_risk_score"] > 70
    assert assessment["risk_level"] in ["high", "critical"]


def test_assessment_has_required_fields():
    """Test that assessment contains all required fields."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(SECURE_TELEMETRY)
    
    required_fields = [
        "assessment_time",
        "total_risk_score",
        "risk_level",
        "component_scores",
        "risk_factors",
        "recommendations"
    ]
    
    for field in required_fields:
        assert field in assessment, f"Missing field: {field}"


def test_component_scores():
    """Test that component scores are calculated."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(SECURE_TELEMETRY)
    
    scores = assessment["component_scores"]
    
    assert "security_posture" in scores
    assert "compliance" in scores
    assert "behavioral" in scores
    assert "threat_indicators" in scores
    
    # All scores should be between 0 and 100
    for score_name, score_value in scores.items():
        assert 0 <= score_value <= 100, f"{score_name} score out of range: {score_value}"


def test_risk_factors_for_insecure_device():
    """Test that risk factors are identified for insecure devices."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(INSECURE_TELEMETRY)
    
    risk_factors = assessment["risk_factors"]
    
    assert len(risk_factors) > 0, "Should identify risk factors"
    
    # Check that critical issues are flagged
    factor_names = [f["factor_name"] for f in risk_factors]
    assert any("FileVault" in name for name in factor_names)


def test_recommendations_generated():
    """Test that recommendations are generated for risky devices."""
    assessor = RiskAssessor()
    assessment = assessor.assess_device_risk(INSECURE_TELEMETRY)
    
    recommendations = assessment["recommendations"]
    
    assert len(recommendations) > 0, "Should generate recommendations"
    assert all("action" in rec for rec in recommendations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

