"""
Base Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Abstract base class for all security tool integrations.
"""

from abc import ABC, abstractmethod
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List, Optional
import logging
import time
import httpx

from integrations.models import Integration, SyncStatus


logger = logging.getLogger(__name__)


class BaseIntegrationConnector(ABC):
    """
    Abstract base class for integration connectors.
    
    Provides common functionality for API communication, authentication,
    rate limiting, and error handling.
    """
    
    def __init__(self, integration: Integration):
        """
        Initialize connector.
        
        Args:
            integration: Integration configuration
        """
        self.integration = integration
        self.client = None
        self._token_refresh_task = None
        
        # Rate limiting
        self._request_timestamps: List[float] = []
    
    @abstractmethod
    def get_integration_type(self) -> str:
        """
        Get integration type identifier.
        
        Returns:
            Integration type string
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the external service.
        
        Returns:
            Dictionary with connection test results
        """
        pass
    
    @abstractmethod
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from external system.
        
        Returns:
            Dictionary with sync results
        """
        pass
    
    @abstractmethod
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from external system.
        
        Returns:
            Dictionary with sync results
        """
        pass
    
    @abstractmethod
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync policy data from external system.
        
        Returns:
            Dictionary with sync results
        """
        pass
    
    @abstractmethod
    async def push_compliance_status(self, device_id: str, status: Dict[str, Any]) -> bool:
        """
        Push compliance status to external system.
        
        Args:
            device_id: Device identifier
            status: Compliance status data
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def push_risk_score(self, device_id: str, risk_score: Dict[str, Any]) -> bool:
        """
        Push risk score to external system.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Process webhook payload from external system.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event data
        """
        pass
    
    def get_http_client(self) -> httpx.AsyncClient:
        """
        Get configured HTTP client.
        
        Returns:
            Configured httpx client
        """
        if self.client is None:
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            self.client = httpx.AsyncClient(
                timeout=timeout,
                verify=True,  # SSL verification
                follow_redirects=True
            )
        
        return self.client
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Dictionary of auth headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ZeroTrust-Mac-Compliance/0.9.7"
        }
        
        if self.integration.auth_type == "bearer":
            if self.integration.access_token:
                headers["Authorization"] = f"Bearer {self.integration.access_token}"
            elif self.integration.api_key:
                headers["Authorization"] = f"Bearer {self.integration.api_key}"
        
        elif self.integration.auth_type == "api_key":
            # Integration-specific header name (override in subclass)
            headers["X-API-Key"] = self.integration.api_key
        
        elif self.integration.auth_type == "basic":
            # Basic auth handled by httpx auth parameter
            pass
        
        return headers
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
        
        Returns:
            Response object
        """
        # Rate limiting
        await self._check_rate_limit()
        
        # Build full URL
        url = f"{self.integration.endpoint.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Add auth headers
        headers = kwargs.get("headers", {})
        auth_headers = self.get_auth_headers()
        headers.update(auth_headers)
        kwargs["headers"] = headers
        
        # Retry logic
        max_retries = 3
        retry_delay = 1.0
        
        client = self.get_http_client()
        
        for attempt in range(max_retries):
            try:
                response = await client.request(method, url, **kwargs)
                
                # Check for rate limiting response
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                
                # Check for auth errors
                if response.status_code == 401:
                    # Try to refresh token
                    if await self._refresh_token():
                        continue  # Retry with new token
                
                return response
            
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise
                
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(retry_delay * (2 ** attempt))
        
        raise Exception("Max retries exceeded")
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = time.time()
        
        # Remove old timestamps
        cutoff = now - self.integration.rate_limit_period_seconds
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > cutoff
        ]
        
        # Check if limit exceeded
        if len(self._request_timestamps) >= self.integration.rate_limit_requests:
            # Calculate wait time
            oldest = self._request_timestamps[0]
            wait_time = self.integration.rate_limit_period_seconds - (now - oldest)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self._request_timestamps.append(now)
    
    async def _refresh_token(self) -> bool:
        """
        Refresh OAuth2 access token.
        
        Returns:
            True if token refreshed successfully
        """
        # Override in subclass if OAuth2 is used
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status dictionary
        """
        # Run test_connection synchronously for health check
        import asyncio
        try:
            result = asyncio.run(self.test_connection())
            
            return {
                "healthy": result.get("success", False),
                "status": "healthy" if result.get("success") else "unhealthy",
                "integration_id": self.integration.integration_id,
                "integration_type": self.get_integration_type(),
                "last_check": datetime.now(UTC).isoformat(),
                "details": result
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "status": "unhealthy",
                "integration_id": self.integration.integration_id,
                "integration_type": self.get_integration_type(),
                "last_check": datetime.now(UTC).isoformat(),
                "error": str(e)
            }
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from headers
        
        Returns:
            True if signature is valid
        """
        if not self.integration.webhook_secret:
            return True  # No validation configured
        
        # Override in subclass for specific signature algorithms
        import hmac
        import hashlib
        
        expected = hmac.new(
            self.integration.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    async def full_sync(self) -> Dict[str, Any]:
        """
        Perform full synchronization of all data.
        
        Returns:
            Dictionary with sync results
        """
        results = {
            "devices": None,
            "users": None,
            "policies": None,
            "success": True,
            "errors": []
        }
        
        try:
            if self.integration.sync_devices:
                results["devices"] = await self.sync_devices()
        except Exception as e:
            logger.error(f"Device sync failed: {e}")
            results["errors"].append(f"Devices: {str(e)}")
            results["success"] = False
        
        try:
            if self.integration.sync_users:
                results["users"] = await self.sync_users()
        except Exception as e:
            logger.error(f"User sync failed: {e}")
            results["errors"].append(f"Users: {str(e)}")
            results["success"] = False
        
        try:
            if self.integration.sync_policies:
                results["policies"] = await self.sync_policies()
        except Exception as e:
            logger.error(f"Policy sync failed: {e}")
            results["errors"].append(f"Policies: {str(e)}")
            results["success"] = False
        
        return results


# Import asyncio at module level
import asyncio

