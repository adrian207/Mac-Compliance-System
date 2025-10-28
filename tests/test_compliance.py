"""
Compliance Checker Tests

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from hardening.compliance_checker import ComplianceChecker


COMPLIANT_TELEMETRY = {
    "system_info": {
        "os_version": "14.0"
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
    }
}

NON_COMPLIANT_TELEMETRY = {
    "system_info": {
        "os_version": "11.0"
    },
    "security_status": {
        "filevault_enabled": False,
        "firewall_enabled": False,
        "gatekeeper_enabled": False,
        "sip_enabled": False
    },
    "authentication": {
        "password_required": False,
        "screen_lock_enabled": False
    }
}


def test_compliance_checker_initialization():
    """Test compliance checker initializes."""
    checker = ComplianceChecker()
    assert checker is not None


def test_compliant_device_passes():
    """Test that a compliant device passes checks."""
    checker = ComplianceChecker()
    result = checker.check_compliance(COMPLIANT_TELEMETRY)
    
    assert result["compliance_score"] > 80
    assert len(result["violations"]) < 3


def test_non_compliant_device_fails():
    """Test that a non-compliant device fails checks."""
    checker = ComplianceChecker()
    result = checker.check_compliance(NON_COMPLIANT_TELEMETRY)
    
    assert result["is_compliant"] is False
    assert len(result["violations"]) > 0


def test_compliance_result_structure():
    """Test compliance result has required fields."""
    checker = ComplianceChecker()
    result = checker.check_compliance(COMPLIANT_TELEMETRY)
    
    required_fields = [
        "is_compliant",
        "compliance_score",
        "total_checks",
        "passed_checks",
        "failed_checks",
        "violations",
        "check_results"
    ]
    
    for field in required_fields:
        assert field in result, f"Missing field: {field}"


def test_violations_have_severity():
    """Test that violations include severity levels."""
    checker = ComplianceChecker()
    result = checker.check_compliance(NON_COMPLIANT_TELEMETRY)
    
    for violation in result["violations"]:
        assert "severity" in violation
        assert violation["severity"] in ["low", "medium", "high", "critical"]


def test_remediation_actions_generated():
    """Test that remediation actions are provided."""
    checker = ComplianceChecker()
    result = checker.check_compliance(NON_COMPLIANT_TELEMETRY)
    
    if not result["is_compliant"]:
        assert result["remediation_required"] is True
        assert len(result["remediation_actions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

