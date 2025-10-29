"""
CrowdStrike Falcon Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Integrates with CrowdStrike Falcon for endpoint detection and response (EDR),
threat intelligence, and real-time security monitoring.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import logging

from integrations.connectors.base import BaseIntegrationConnector
from integrations.models import Integration


logger = logging.getLogger(__name__)


class CrowdStrikeConnector(BaseIntegrationConnector):
    """
    CrowdStrike Falcon integration connector.
    
    Provides EDR capabilities, threat detection, and security monitoring
    through CrowdStrike Falcon API.
    
    API Documentation: https://falcon.crowdstrike.com/documentation/
    """
    
    def __init__(self, integration: Integration):
        """Initialize CrowdStrike connector."""
        super().__init__(integration)
        self._access_token = None
        self._token_expires = None
    
    def get_integration_type(self) -> str:
        """Get integration type."""
        return "crowdstrike"
    
    async def _authenticate(self) -> bool:
        """
        Authenticate with CrowdStrike and obtain OAuth2 token.
        
        Returns:
            True if authentication successful
        """
        try:
            import base64
            
            # Prepare client credentials
            credentials = f"{self.integration.client_id}:{self.integration.client_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = await self.make_request(
                "POST",
                "/oauth2/token",
                headers=headers,
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code == 201:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires = datetime.now(UTC).timestamp() + expires_in
                logger.info("CrowdStrike authentication successful")
                return True
            
            logger.error(f"CrowdStrike authentication failed: HTTP {response.status_code}")
            return False
        
        except Exception as e:
            logger.error(f"CrowdStrike authentication error: {e}")
            return False
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure valid authentication token exists."""
        if not self._access_token or not self._token_expires:
            return await self._authenticate()
        
        if datetime.now(UTC).timestamp() >= self._token_expires - 300:  # Refresh 5 min before expiry
            logger.info("CrowdStrike token expired, re-authenticating")
            return await self._authenticate()
        
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get CrowdStrike-specific authentication headers."""
        headers = super().get_auth_headers()
        
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        
        return headers
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test CrowdStrike API connection.
        
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
            response = await self.make_request("GET", "/sensors/queries/sensors/v1?limit=1")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to CrowdStrike Falcon",
                    "api_version": "v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: HTTP {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"CrowdStrike connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from CrowdStrike.
        
        Retrieves hosts with Falcon sensor installed.
        
        Returns:
            Sync results
        """
        try:
            if not await self._ensure_authenticated():
                return {"success": False, "error": "Authentication failed"}
            
            # Get device IDs
            response = await self.make_request(
                "GET",
                "/devices/queries/devices/v1?limit=5000"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            device_ids = response.json().get("resources", [])
            
            if not device_ids:
                return {
                    "success": True,
                    "devices_synced": 0,
                    "devices": []
                }
            
            # Get device details (in batches of 100)
            all_devices = []
            for i in range(0, len(device_ids), 100):
                batch_ids = device_ids[i:i+100]
                
                response = await self.make_request(
                    "POST",
                    "/devices/entities/devices/v2",
                    json={"ids": batch_ids}
                )
                
                if response.status_code == 200:
                    devices = response.json().get("resources", [])
                    all_devices.extend(devices)
            
            # Process devices
            processed_devices = []
            for device in all_devices:
                processed = self._process_device(device)
                if processed:
                    processed_devices.append(processed)
            
            return {
                "success": True,
                "devices_synced": len(processed_devices),
                "devices": processed_devices
            }
        
        except Exception as e:
            logger.error(f"CrowdStrike device sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_device(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process device data from CrowdStrike."""
        try:
            return {
                "external_id": device_data.get("device_id"),
                "device_name": device_data.get("hostname"),
                "platform": device_data.get("platform_name"),
                "os_version": device_data.get("os_version"),
                
                # CrowdStrike specific
                "agent_version": device_data.get("agent_version"),
                "agent_local_time": device_data.get("agent_local_time"),
                "sensor_status": device_data.get("status"),
                
                # User
                "current_user": device_data.get("last_seen"),
                
                # Network
                "local_ip": device_data.get("local_ip"),
                "external_ip": device_data.get("external_ip"),
                "mac_address": device_data.get("mac_address"),
                
                # System
                "system_manufacturer": device_data.get("system_manufacturer"),
                "system_product_name": device_data.get("system_product_name"),
                "bios_version": device_data.get("bios_version"),
                
                # Timestamps
                "first_seen": device_data.get("first_seen"),
                "last_seen": device_data.get("last_seen"),
                
                # Status
                "reduced_functionality_mode": device_data.get("reduced_functionality_mode"),
                
                # Metadata
                "source": "crowdstrike",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing CrowdStrike device: {e}")
            return None
    
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from CrowdStrike.
        
        CrowdStrike doesn't have user management; returns empty.
        
        Returns:
            Sync results
        """
        return {
            "success": True,
            "users_synced": 0,
            "users": [],
            "note": "CrowdStrike does not provide user management"
        }
    
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync prevention policies from CrowdStrike.
        
        Returns:
            Sync results
        """
        try:
            if not await self._ensure_authenticated():
                return {"success": False, "error": "Authentication failed"}
            
            # Get prevention policies
            response = await self.make_request(
                "GET",
                "/policy/combined/prevention/v1"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            policies = response.json().get("resources", [])
            
            # Process policies
            processed_policies = []
            for policy in policies:
                processed = self._process_policy(policy)
                if processed:
                    processed_policies.append(processed)
            
            return {
                "success": True,
                "policies_synced": len(processed_policies),
                "policies": processed_policies
            }
        
        except Exception as e:
            logger.error(f"CrowdStrike policy sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_policy(self, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process policy data from CrowdStrike."""
        try:
            return {
                "external_id": policy_data.get("id"),
                "name": policy_data.get("name"),
                "description": policy_data.get("description"),
                "type": "prevention",
                "platform": policy_data.get("platform_name"),
                "enabled": policy_data.get("enabled", False),
                "created_by": policy_data.get("created_by"),
                "created_timestamp": policy_data.get("created_timestamp"),
                "source": "crowdstrike",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing CrowdStrike policy: {e}")
            return None
    
    async def get_detections(
        self,
        device_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get threat detections from CrowdStrike.
        
        Args:
            device_id: Optional device ID filter
            hours: Hours to look back
        
        Returns:
            List of detections
        """
        try:
            if not await self._ensure_authenticated():
                return []
            
            # Build filter
            filter_query = f"last_behavior:>='{hours}h'"
            if device_id:
                filter_query += f"+device_id:'{device_id}'"
            
            # Get detection IDs
            response = await self.make_request(
                "GET",
                f"/detects/queries/detects/v1?filter={filter_query}&limit=1000"
            )
            
            if response.status_code != 200:
                return []
            
            detection_ids = response.json().get("resources", [])
            
            if not detection_ids:
                return []
            
            # Get detection details
            response = await self.make_request(
                "POST",
                "/detects/entities/summaries/GET/v1",
                json={"ids": detection_ids}
            )
            
            if response.status_code == 200:
                return response.json().get("resources", [])
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting CrowdStrike detections: {e}")
            return []
    
    async def push_compliance_status(
        self,
        device_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """
        Push compliance status to CrowdStrike.
        
        CrowdStrike doesn't accept external compliance data.
        This logs for reference.
        
        Args:
            device_id: Device identifier
            status: Compliance status
        
        Returns:
            True (logged only)
        """
        logger.info(f"Compliance status for {device_id}: {status.get('is_compliant')}")
        return True
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> bool:
        """
        Push risk score to CrowdStrike.
        
        CrowdStrike doesn't accept external risk scores.
        This logs for reference.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True (logged only)
        """
        logger.info(f"Risk score for {device_id}: {risk_score.get('total_risk_score')}")
        return True
    
    async def contain_host(self, device_id: str) -> bool:
        """
        Network contain a host (isolate from network).
        
        Args:
            device_id: CrowdStrike device ID
        
        Returns:
            True if successful
        """
        try:
            if not await self._ensure_authenticated():
                return False
            
            payload = {
                "ids": [device_id]
            }
            
            response = await self.make_request(
                "POST",
                "/devices/entities/devices-actions/v2?action_name=contain",
                json=payload
            )
            
            return response.status_code in [200, 202]
        
        except Exception as e:
            logger.error(f"Error containing CrowdStrike host: {e}")
            return False
    
    async def lift_containment(self, device_id: str) -> bool:
        """
        Lift network containment from a host.
        
        Args:
            device_id: CrowdStrike device ID
        
        Returns:
            True if successful
        """
        try:
            if not await self._ensure_authenticated():
                return False
            
            payload = {
                "ids": [device_id]
            }
            
            response = await self.make_request(
                "POST",
                "/devices/entities/devices-actions/v2?action_name=lift_containment",
                json=payload
            )
            
            return response.status_code in [200, 202]
        
        except Exception as e:
            logger.error(f"Error lifting CrowdStrike containment: {e}")
            return False
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process webhook from CrowdStrike.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event
        """
        event_type = payload.get("event_type")
        
        if event_type == "DetectionSummaryEvent":
            return self._process_detection_event(payload)
        elif event_type == "IncidentSummaryEvent":
            return self._process_incident_event(payload)
        elif event_type == "AuthActivityAuditEvent":
            return self._process_auth_event(payload)
        else:
            return {
                "event_type": event_type,
                "processed": False,
                "message": f"Unknown event type: {event_type}"
            }
    
    def _process_detection_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process detection event."""
        return {
            "event_type": "detection",
            "detection_id": payload.get("detection_id"),
            "device_id": payload.get("device", {}).get("device_id"),
            "hostname": payload.get("device", {}).get("hostname"),
            "severity": payload.get("severity"),
            "tactic": payload.get("tactic"),
            "technique": payload.get("technique"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_incident_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incident event."""
        return {
            "event_type": "incident",
            "incident_id": payload.get("incident_id"),
            "name": payload.get("name"),
            "severity": payload.get("severity"),
            "hosts_impacted": payload.get("hosts", {}).get("count", 0),
            "timestamp": payload.get("start"),
            "processed": True
        }
    
    def _process_auth_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process authentication event."""
        return {
            "event_type": "authentication",
            "user_id": payload.get("UserId"),
            "user_name": payload.get("UserName"),
            "operation": payload.get("OperationName"),
            "success": payload.get("Success"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }

