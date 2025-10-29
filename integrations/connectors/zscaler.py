"""
Zscaler Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Integrates with Zscaler ZIA (Internet Access) and ZPA (Private Access)
for Zero Trust network security.
"""

from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List, Optional
import logging
import hashlib
import time

from integrations.connectors.base import BaseIntegrationConnector
from integrations.models import Integration


logger = logging.getLogger(__name__)


class ZscalerConnector(BaseIntegrationConnector):
    """
    Zscaler integration connector.
    
    Supports both ZIA (Internet Access) and ZPA (Private Access) APIs.
    
    API Documentation:
    - ZIA: https://help.zscaler.com/zia/api
    - ZPA: https://help.zscaler.com/zpa/api
    """
    
    def __init__(self, integration: Integration):
        """Initialize Zscaler connector."""
        super().__init__(integration)
        self._session_token = None
        self._session_expires = None
    
    def get_integration_type(self) -> str:
        """Get integration type."""
        return "zscaler"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get Zscaler-specific authentication headers.
        
        Returns:
            Dictionary of headers
        """
        headers = super().get_auth_headers()
        
        # Add session cookie if authenticated
        if self._session_token:
            headers["Cookie"] = f"JSESSIONID={self._session_token}"
        
        return headers
    
    async def _authenticate(self) -> bool:
        """
        Authenticate with Zscaler and obtain session token.
        
        Zscaler uses a unique authentication mechanism with obfuscated API key.
        
        Returns:
            True if authentication successful
        """
        try:
            # Get current timestamp in milliseconds
            timestamp = str(int(time.time() * 1000))
            
            # Obfuscate API key with timestamp
            # API key is shifted by timestamp for security
            obfuscated_key = self._obfuscate_api_key(
                self.integration.api_key,
                timestamp
            )
            
            payload = {
                "apiKey": obfuscated_key,
                "username": self.integration.client_id,  # Admin username
                "password": self.integration.client_secret,  # Admin password
                "timestamp": timestamp
            }
            
            # Authenticate
            response = await self.make_request(
                "POST",
                "/api/v1/authenticatedSession",
                json=payload
            )
            
            if response.status_code == 200:
                # Extract session token from Set-Cookie header
                set_cookie = response.headers.get("Set-Cookie", "")
                if "JSESSIONID=" in set_cookie:
                    self._session_token = set_cookie.split("JSESSIONID=")[1].split(";")[0]
                    # Session typically valid for 30 minutes
                    self._session_expires = datetime.now(UTC) + timedelta(minutes=25)
                    logger.info("Zscaler authentication successful")
                    return True
            
            logger.error(f"Zscaler authentication failed: HTTP {response.status_code}")
            return False
        
        except Exception as e:
            logger.error(f"Zscaler authentication error: {e}")
            return False
    
    def _obfuscate_api_key(self, api_key: str, timestamp: str) -> str:
        """
        Obfuscate API key using Zscaler's algorithm.
        
        Args:
            api_key: Raw API key
            timestamp: Current timestamp in milliseconds
        
        Returns:
            Obfuscated API key
        """
        # Zscaler's key obfuscation algorithm
        seed = api_key
        now = timestamp
        n = str(int(now) >> 1)
        r = str((int(n) + int(api_key[:6])))
        key = ""
        
        for i in range(len(str(n))):
            key += seed[int(str(n)[i])]
        
        for j in range(len(str(r))):
            key += seed[int(str(r)[j]) + 2]
        
        return key
    
    async def _ensure_authenticated(self) -> bool:
        """
        Ensure valid authentication session exists.
        
        Returns:
            True if authenticated
        """
        # Check if session expired
        if not self._session_token or not self._session_expires:
            return await self._authenticate()
        
        if datetime.now(UTC) >= self._session_expires:
            logger.info("Zscaler session expired, re-authenticating")
            return await self._authenticate()
        
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Zscaler API connection.
        
        Returns:
            Connection test results
        """
        try:
            if not await self._ensure_authenticated():
                return {
                    "success": False,
                    "message": "Authentication failed"
                }
            
            # Test API call
            response = await self.make_request("GET", "/api/v1/status")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to Zscaler",
                    "api_version": "v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: HTTP {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Zscaler connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from Zscaler.
        
        Retrieves enrolled devices and their network access policies.
        
        Returns:
            Sync results
        """
        try:
            if not await self._ensure_authenticated():
                return {"success": False, "error": "Authentication failed"}
            
            # Get devices (ZIA endpoint)
            response = await self.make_request("GET", "/api/v1/devices")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            devices_data = response.json()
            
            # Process devices
            processed_devices = []
            for device in devices_data:
                processed = self._process_device(device)
                if processed:
                    processed_devices.append(processed)
            
            return {
                "success": True,
                "devices_synced": len(processed_devices),
                "devices": processed_devices
            }
        
        except Exception as e:
            logger.error(f"Zscaler device sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_device(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process device data from Zscaler."""
        try:
            return {
                "external_id": device_data.get("id"),
                "device_name": device_data.get("name"),
                "owner": device_data.get("owner"),
                "device_type": device_data.get("deviceType"),
                "os_type": device_data.get("osType"),
                "os_version": device_data.get("osVersion"),
                
                # Zscaler-specific
                "model": device_data.get("deviceModel"),
                "description": device_data.get("description"),
                
                # Network
                "hostname": device_data.get("hostname"),
                
                # Metadata
                "source": "zscaler",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Zscaler device: {e}")
            return None
    
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from Zscaler.
        
        Returns:
            Sync results
        """
        try:
            if not await self._ensure_authenticated():
                return {"success": False, "error": "Authentication failed"}
            
            # Get users
            response = await self.make_request(
                "GET",
                "/api/v1/users?pageSize=1000"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            users_data = response.json()
            
            # Process users
            processed_users = []
            for user in users_data:
                processed = self._process_user(user)
                if processed:
                    processed_users.append(processed)
            
            return {
                "success": True,
                "users_synced": len(processed_users),
                "users": processed_users
            }
        
        except Exception as e:
            logger.error(f"Zscaler user sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process user data from Zscaler."""
        try:
            return {
                "external_id": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "department": user_data.get("department"),
                "groups": user_data.get("groups", []),
                "source": "zscaler",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Zscaler user: {e}")
            return None
    
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync access policies from Zscaler.
        
        Returns:
            Sync results
        """
        try:
            if not await self._ensure_authenticated():
                return {"success": False, "error": "Authentication failed"}
            
            # Get URL filtering policies (ZIA)
            response = await self.make_request(
                "GET",
                "/api/v1/urlFilteringRules"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            policies_data = response.json()
            
            # Process policies
            processed_policies = []
            for policy in policies_data:
                processed = self._process_policy(policy)
                if processed:
                    processed_policies.append(processed)
            
            return {
                "success": True,
                "policies_synced": len(processed_policies),
                "policies": processed_policies
            }
        
        except Exception as e:
            logger.error(f"Zscaler policy sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_policy(self, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process policy data from Zscaler."""
        try:
            return {
                "external_id": policy_data.get("id"),
                "name": policy_data.get("name"),
                "description": policy_data.get("description"),
                "type": "url_filtering",
                "action": policy_data.get("action"),
                "state": policy_data.get("state"),
                "order": policy_data.get("order"),
                "enabled": policy_data.get("enabled", False),
                "source": "zscaler",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Zscaler policy: {e}")
            return None
    
    async def get_user_risk_score(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        Get risk score for a user from Zscaler.
        
        Args:
            user_email: User email address
        
        Returns:
            User risk score
        """
        try:
            if not await self._ensure_authenticated():
                return None
            
            response = await self.make_request(
                "GET",
                f"/api/v1/users/{user_email}/riskScore"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting Zscaler user risk score: {e}")
            return None
    
    async def push_compliance_status(
        self,
        device_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """
        Push compliance status to Zscaler.
        
        Updates device trust level based on compliance.
        
        Args:
            device_id: Device identifier
            status: Compliance status
        
        Returns:
            True if successful
        """
        try:
            if not await self._ensure_authenticated():
                return False
            
            # Map compliance to trust level
            trust_level = "HIGH" if status.get("is_compliant") else "LOW"
            
            payload = {
                "deviceId": device_id,
                "trustLevel": trust_level,
                "complianceScore": status.get("compliance_score", 0),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "PUT",
                f"/api/v1/devices/{device_id}/trustLevel",
                json=payload
            )
            
            return response.status_code in [200, 204]
        
        except Exception as e:
            logger.error(f"Error pushing compliance to Zscaler: {e}")
            return False
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> bool:
        """
        Push risk score to Zscaler.
        
        Updates device posture based on risk assessment.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True if successful
        """
        try:
            if not await self._ensure_authenticated():
                return False
            
            payload = {
                "deviceId": device_id,
                "riskScore": risk_score.get("total_risk_score", 0),
                "riskLevel": risk_score.get("risk_level", "unknown"),
                "riskFactors": risk_score.get("risk_factors", []),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "PUT",
                f"/api/v1/devices/{device_id}/posture",
                json=payload
            )
            
            return response.status_code in [200, 204]
        
        except Exception as e:
            logger.error(f"Error pushing risk score to Zscaler: {e}")
            return False
    
    async def update_access_policy(
        self,
        device_id: str,
        policy_action: str
    ) -> bool:
        """
        Update network access policy for device.
        
        Args:
            device_id: Device identifier
            policy_action: Action (allow, block, isolate)
        
        Returns:
            True if successful
        """
        try:
            if not await self._ensure_authenticated():
                return False
            
            payload = {
                "deviceId": device_id,
                "action": policy_action,
                "updatedAt": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "POST",
                f"/api/v1/devices/{device_id}/accessPolicy",
                json=payload
            )
            
            return response.status_code in [200, 201]
        
        except Exception as e:
            logger.error(f"Error updating Zscaler access policy: {e}")
            return False
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process webhook from Zscaler.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event
        """
        event_type = payload.get("eventType")
        
        if event_type == "user.risk.changed":
            return self._process_risk_changed(payload)
        elif event_type == "device.posture.changed":
            return self._process_posture_changed(payload)
        elif event_type == "threat.detected":
            return self._process_threat_detected(payload)
        elif event_type == "policy.violation":
            return self._process_policy_violation(payload)
        else:
            return {
                "event_type": event_type,
                "processed": False,
                "message": f"Unknown event type: {event_type}"
            }
    
    def _process_risk_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk changed webhook."""
        return {
            "event_type": "risk_changed",
            "user_email": payload.get("userEmail"),
            "old_risk_score": payload.get("oldRiskScore"),
            "new_risk_score": payload.get("newRiskScore"),
            "risk_factors": payload.get("riskFactors", []),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_posture_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process posture changed webhook."""
        return {
            "event_type": "posture_changed",
            "device_id": payload.get("deviceId"),
            "old_posture": payload.get("oldPosture"),
            "new_posture": payload.get("newPosture"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_threat_detected(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process threat detected webhook."""
        return {
            "event_type": "threat_detected",
            "user_email": payload.get("userEmail"),
            "device_id": payload.get("deviceId"),
            "threat_type": payload.get("threatType"),
            "threat_name": payload.get("threatName"),
            "severity": payload.get("severity"),
            "url": payload.get("url"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_policy_violation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process policy violation webhook."""
        return {
            "event_type": "policy_violation",
            "user_email": payload.get("userEmail"),
            "device_id": payload.get("deviceId"),
            "policy_id": payload.get("policyId"),
            "policy_name": payload.get("policyName"),
            "action": payload.get("action"),
            "url": payload.get("url"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    async def close(self):
        """Close connection and logout."""
        if self._session_token:
            try:
                await self.make_request("DELETE", "/api/v1/authenticatedSession")
                logger.info("Zscaler session closed")
            except Exception as e:
                logger.error(f"Error closing Zscaler session: {e}")
        
        await super().close()

