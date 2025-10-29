"""
Seraphic Browser Security Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Integrates with Seraphic browser security platform for enterprise browser
isolation and threat protection.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import logging

from integrations.connectors.base import BaseIntegrationConnector
from integrations.models import Integration


logger = logging.getLogger(__name__)


class SeraphicConnector(BaseIntegrationConnector):
    """
    Seraphic browser security integration connector.
    
    Provides browser isolation, threat detection, and data protection
    through Seraphic's enterprise browser security platform.
    
    API Documentation: https://api.seraphicsecurity.com/docs
    """
    
    def get_integration_type(self) -> str:
        """Get integration type."""
        return "seraphic"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get Seraphic-specific authentication headers.
        
        Returns:
            Dictionary of headers
        """
        headers = super().get_auth_headers()
        
        # Seraphic uses API key authentication
        if self.integration.api_key:
            headers["X-Seraphic-API-Key"] = self.integration.api_key
        
        return headers
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Seraphic API connection.
        
        Returns:
            Connection test results
        """
        try:
            response = await self.make_request("GET", "/api/v1/health")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": "Successfully connected to Seraphic",
                    "api_version": data.get("version", "v1"),
                    "tenant_id": data.get("tenantId")
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: HTTP {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Seraphic connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from Seraphic.
        
        Retrieves devices with browser security agent installed.
        
        Returns:
            Sync results
        """
        try:
            devices = []
            page = 1
            has_more = True
            
            while has_more:
                response = await self.make_request(
                    "GET",
                    f"/api/v1/endpoints?page={page}&limit=100"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    devices.extend(data.get("endpoints", []))
                    has_more = data.get("hasMore", False)
                    page += 1
                else:
                    break
            
            # Process devices
            processed_devices = []
            for device in devices:
                processed = self._process_device(device)
                if processed:
                    processed_devices.append(processed)
            
            return {
                "success": True,
                "devices_synced": len(processed_devices),
                "devices": processed_devices
            }
        
        except Exception as e:
            logger.error(f"Seraphic device sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_device(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process device data from Seraphic."""
        try:
            return {
                "external_id": device_data.get("endpointId"),
                "device_name": device_data.get("hostname"),
                "user_email": device_data.get("userEmail"),
                "platform": device_data.get("platform"),
                "os_version": device_data.get("osVersion"),
                
                # Browser security
                "agent_version": device_data.get("agentVersion"),
                "agent_status": device_data.get("agentStatus"),
                "last_seen": device_data.get("lastSeen"),
                
                # Protection status
                "protection_enabled": device_data.get("protectionEnabled", False),
                "isolation_enabled": device_data.get("isolationEnabled", False),
                "dlp_enabled": device_data.get("dlpEnabled", False),
                
                # Policy
                "policy_id": device_data.get("policyId"),
                "policy_name": device_data.get("policyName"),
                
                # Metadata
                "source": "seraphic",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Seraphic device: {e}")
            return None
    
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from Seraphic.
        
        Returns:
            Sync results
        """
        try:
            response = await self.make_request(
                "GET",
                "/api/v1/users?limit=1000"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            users_data = response.json()
            users = users_data.get("users", [])
            
            # Process users
            processed_users = []
            for user in users:
                processed = self._process_user(user)
                if processed:
                    processed_users.append(processed)
            
            return {
                "success": True,
                "users_synced": len(processed_users),
                "users": processed_users
            }
        
        except Exception as e:
            logger.error(f"Seraphic user sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process user data from Seraphic."""
        try:
            return {
                "external_id": user_data.get("userId"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "department": user_data.get("department"),
                "endpoint_count": user_data.get("endpointCount", 0),
                "source": "seraphic",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Seraphic user: {e}")
            return None
    
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync security policies from Seraphic.
        
        Returns:
            Sync results
        """
        try:
            response = await self.make_request("GET", "/api/v1/policies")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            policies_data = response.json()
            policies = policies_data.get("policies", [])
            
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
            logger.error(f"Seraphic policy sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_policy(self, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process policy data from Seraphic."""
        try:
            return {
                "external_id": policy_data.get("policyId"),
                "name": policy_data.get("name"),
                "description": policy_data.get("description"),
                "type": "browser_security",
                "enabled": policy_data.get("enabled", False),
                "endpoint_count": policy_data.get("endpointCount", 0),
                "settings": policy_data.get("settings", {}),
                "source": "seraphic",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Seraphic policy: {e}")
            return None
    
    async def get_threat_detections(
        self,
        device_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get threat detections from Seraphic.
        
        Args:
            device_id: Optional device ID filter
            hours: Hours to look back
        
        Returns:
            List of threat detections
        """
        try:
            params = {
                "hours": hours
            }
            
            if device_id:
                params["endpointId"] = device_id
            
            response = await self.make_request(
                "GET",
                "/api/v1/threats",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("threats", [])
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting Seraphic threats: {e}")
            return []
    
    async def push_compliance_status(
        self,
        device_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """
        Push compliance status to Seraphic.
        
        Updates device trust level based on compliance.
        
        Args:
            device_id: Device identifier
            status: Compliance status
        
        Returns:
            True if successful
        """
        try:
            payload = {
                "endpointId": device_id,
                "compliant": status.get("is_compliant", False),
                "complianceScore": status.get("compliance_score", 0),
                "violations": status.get("violations", []),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "POST",
                f"/api/v1/endpoints/{device_id}/compliance",
                json=payload
            )
            
            return response.status_code in [200, 201, 204]
        
        except Exception as e:
            logger.error(f"Error pushing compliance to Seraphic: {e}")
            return False
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> bool:
        """
        Push risk score to Seraphic.
        
        Updates device risk posture.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True if successful
        """
        try:
            payload = {
                "endpointId": device_id,
                "riskScore": risk_score.get("total_risk_score", 0),
                "riskLevel": risk_score.get("risk_level", "unknown"),
                "riskFactors": risk_score.get("risk_factors", []),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "POST",
                f"/api/v1/endpoints/{device_id}/risk",
                json=payload
            )
            
            return response.status_code in [200, 201, 204]
        
        except Exception as e:
            logger.error(f"Error pushing risk score to Seraphic: {e}")
            return False
    
    async def update_protection_policy(
        self,
        device_id: str,
        policy_action: str
    ) -> bool:
        """
        Update browser protection policy for device.
        
        Args:
            device_id: Device identifier
            policy_action: Action (enable, disable, isolate)
        
        Returns:
            True if successful
        """
        try:
            payload = {
                "endpointId": device_id,
                "action": policy_action,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "POST",
                f"/api/v1/endpoints/{device_id}/policy",
                json=payload
            )
            
            return response.status_code in [200, 201]
        
        except Exception as e:
            logger.error(f"Error updating Seraphic policy: {e}")
            return False
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process webhook from Seraphic.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event
        """
        event_type = payload.get("eventType")
        
        if event_type == "threat.detected":
            return self._process_threat_detected(payload)
        elif event_type == "dlp.violation":
            return self._process_dlp_violation(payload)
        elif event_type == "endpoint.offline":
            return self._process_endpoint_offline(payload)
        elif event_type == "policy.violation":
            return self._process_policy_violation(payload)
        else:
            return {
                "event_type": event_type,
                "processed": False,
                "message": f"Unknown event type: {event_type}"
            }
    
    def _process_threat_detected(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process threat detected webhook."""
        return {
            "event_type": "threat_detected",
            "endpoint_id": payload.get("endpointId"),
            "user_email": payload.get("userEmail"),
            "threat_type": payload.get("threatType"),
            "threat_name": payload.get("threatName"),
            "severity": payload.get("severity"),
            "url": payload.get("url"),
            "action_taken": payload.get("actionTaken"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_dlp_violation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process DLP violation webhook."""
        return {
            "event_type": "dlp_violation",
            "endpoint_id": payload.get("endpointId"),
            "user_email": payload.get("userEmail"),
            "rule_name": payload.get("ruleName"),
            "violation_type": payload.get("violationType"),
            "action": payload.get("action"),
            "url": payload.get("url"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_endpoint_offline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process endpoint offline webhook."""
        return {
            "event_type": "endpoint_offline",
            "endpoint_id": payload.get("endpointId"),
            "user_email": payload.get("userEmail"),
            "last_seen": payload.get("lastSeen"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_policy_violation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process policy violation webhook."""
        return {
            "event_type": "policy_violation",
            "endpoint_id": payload.get("endpointId"),
            "user_email": payload.get("userEmail"),
            "policy_name": payload.get("policyName"),
            "violation_details": payload.get("details"),
            "timestamp": payload.get("timestamp"),
            "processed": True
        }

