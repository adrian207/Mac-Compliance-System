"""
Base Integration Class

Author: Adrian Johnson <adrian207@gmail.com>

Abstract base class for security tool integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time

import httpx

from core.logging_config import get_logger

logger = get_logger(__name__)


class BaseIntegration(ABC):
    """
    Abstract base class for security tool integrations.
    
    Provides common functionality for API communication, error handling,
    and retry logic.
    """
    
    def __init__(
        self,
        api_url: str,
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize integration.
        
        Args:
            api_url: Base API URL
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.client = httpx.Client(timeout=timeout)
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the service.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict of HTTP headers
        """
        pass
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters
            headers: Additional HTTP headers
        
        Returns:
            Response data as dict
        
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self.get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.retry_attempts):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=request_headers
                )
                response.raise_for_status()
                
                # Try to parse JSON response
                try:
                    return response.json()
                except ValueError:
                    return {"success": True, "data": response.text}
            
            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(
                    "request_failed",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                # Wait before retry (exponential backoff)
                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        # All retries failed
        logger.error(
            "request_failed_all_retries",
            method=method,
            url=url,
            error=str(last_exception)
        )
        raise last_exception
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            Response data
        """
        return self._make_request("GET", endpoint, params=params)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body
        
        Returns:
            Response data
        """
        return self._make_request("POST", endpoint, data=data)
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body
        
        Returns:
            Response data
        """
        return self._make_request("PUT", endpoint, data=data)
    
    def delete(
        self,
        endpoint: str
    ) -> Dict[str, Any]:
        """
        Make DELETE request.
        
        Args:
            endpoint: API endpoint
        
        Returns:
            Response data
        """
        return self._make_request("DELETE", endpoint)
    
    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

