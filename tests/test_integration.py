"""
Integration Tests (with mocking)

Author: Adrian Johnson <adrian207@gmail.com>
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.base import BaseIntegration


class MockIntegration(BaseIntegration):
    """Mock integration for testing."""
    
    def test_connection(self):
        return True
    
    def get_auth_headers(self):
        return {"Authorization": "Bearer test-token"}


def test_base_integration_initialization():
    """Test base integration initialization."""
    integration = MockIntegration(
        api_url="https://api.example.com",
        timeout=30,
        retry_attempts=3
    )
    
    assert integration.api_url == "https://api.example.com"
    assert integration.timeout == 30
    assert integration.retry_attempts == 3


def test_integration_get_request():
    """Test integration GET request method."""
    integration = MockIntegration(api_url="https://api.example.com")
    
    with patch.object(integration.client, 'request') as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_request.return_value = mock_response
        
        result = integration.get("/test")
        
        assert result["status"] == "success"
        mock_request.assert_called_once()


def test_integration_post_request():
    """Test integration POST request method."""
    integration = MockIntegration(api_url="https://api.example.com")
    
    with patch.object(integration.client, 'request') as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_request.return_value = mock_response
        
        result = integration.post("/test", data={"key": "value"})
        
        assert result["created"] is True


def test_integration_retry_logic():
    """Test that integration retries on failure."""
    integration = MockIntegration(
        api_url="https://api.example.com",
        retry_attempts=3
    )
    
    with patch.object(integration.client, 'request') as mock_request:
        # First two calls fail with HTTP error, third succeeds
        import httpx
        
        # Create success response
        success_response = Mock()
        success_response.json.return_value = {"status": "success"}
        success_response.status_code = 200
        success_response.raise_for_status = Mock()
        
        # Configure side effects - first two fail, third succeeds
        mock_request.side_effect = [
            httpx.HTTPStatusError("Connection error", request=Mock(), response=Mock()),
            httpx.HTTPStatusError("Connection error", request=Mock(), response=Mock()),
            success_response
        ]
        
        result = integration.get("/test")
        
        assert result["status"] == "success"
        assert mock_request.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

