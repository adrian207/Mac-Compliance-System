"""
API Tests

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns platform info."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_metrics_endpoint():
    """Test metrics endpoint returns Prometheus format."""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    # Check for some expected metrics
    content = response.text
    assert "zerotrust_" in content


def test_risk_assessment_endpoint():
    """Test risk assessment API endpoint."""
    telemetry = {
        "system_info": {"os_version": "14.0", "uuid": "test-123"},
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
        "network_info": {},
        "processes": [],
        "network_connections": []
    }
    
    response = client.post(
        "/api/v1/devices/risk-assessment",
        json={
            "telemetry": telemetry
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "assessment" in data
    assert "total_risk_score" in data["assessment"]
    assert "risk_level" in data["assessment"]


def test_compliance_check_endpoint():
    """Test compliance check API endpoint."""
    telemetry = {
        "system_info": {"os_version": "14.0"},
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
    
    response = client.post(
        "/api/v1/devices/compliance-check",
        json={
            "telemetry": telemetry
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "compliance" in data
    assert "is_compliant" in data["compliance"]
    assert "compliance_score" in data["compliance"]


def test_api_documentation():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

