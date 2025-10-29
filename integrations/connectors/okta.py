"""
Okta SSO Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Integrates with Okta identity and access management platform for
SSO authentication and user context.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import logging

from integrations.connectors.base import BaseIntegrationConnector
from integrations.models import Integration


logger = logging.getLogger(__name__)


class OktaConnector(BaseIntegrationConnector):
    """
    Okta integration connector.
    
    Provides user authentication context, group membership, and SSO integration.
    
    API Documentation: https://developer.okta.com/docs/reference/
    """
    
    def get_integration_type(self) -> str:
        """Get integration type."""
        return "okta"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get Okta-specific authentication headers.
        
        Returns:
            Dictionary of headers
        """
        headers = super().get_auth_headers()
        
        # Okta uses SSWS (Single Sign-On Web Services) token
        if self.integration.api_key:
            headers["Authorization"] = f"SSWS {self.integration.api_key}"
        
        return headers
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Okta API connection.
        
        Returns:
            Connection test results
        """
        try:
            response = await self.make_request("GET", "/api/v1/org")
            
            if response.status_code == 200:
                org_data = response.json()
                return {
                    "success": True,
                    "message": "Successfully connected to Okta",
                    "org_name": org_data.get("companyName"),
                    "org_id": org_data.get("id")
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: HTTP {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Okta connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from Okta.
        
        Okta doesn't have a traditional device inventory, but tracks
        devices through user sessions and device tokens.
        
        Returns:
            Sync results
        """
        try:
            # Get devices registered via Okta Verify
            response = await self.make_request(
                "GET",
                "/api/v1/devices?limit=200"
            )
            
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
            logger.error(f"Okta device sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_device(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process device data from Okta."""
        try:
            return {
                "external_id": device_data.get("id"),
                "device_name": device_data.get("name"),
                "platform": device_data.get("platform"),
                "status": device_data.get("status"),
                
                # User association
                "user_id": device_data.get("userId"),
                
                # Device trust
                "managed": device_data.get("managed", False),
                "registered": device_data.get("registered", False),
                
                # Timestamps
                "created": device_data.get("created"),
                "last_updated": device_data.get("lastUpdated"),
                
                # Metadata
                "source": "okta",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Okta device: {e}")
            return None
    
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from Okta.
        
        Returns:
            Sync results
        """
        try:
            users = []
            url = "/api/v1/users?limit=200"
            
            while url:
                response = await self.make_request("GET", url.replace(self.integration.endpoint, ""))
                
                if response.status_code == 200:
                    batch = response.json()
                    users.extend(batch)
                    
                    # Check for pagination link
                    link_header = response.headers.get("link", "")
                    url = self._parse_next_link(link_header)
                else:
                    break
            
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
            logger.error(f"Okta user sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process user data from Okta."""
        try:
            profile = user_data.get("profile", {})
            
            return {
                "external_id": user_data.get("id"),
                "email": profile.get("email"),
                "login": profile.get("login"),
                "first_name": profile.get("firstName"),
                "last_name": profile.get("lastName"),
                "display_name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
                "department": profile.get("department"),
                "title": profile.get("title"),
                "status": user_data.get("status"),
                "created": user_data.get("created"),
                "last_login": user_data.get("lastLogin"),
                "source": "okta",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Okta user: {e}")
            return None
    
    def _parse_next_link(self, link_header: str) -> Optional[str]:
        """Parse next pagination link from Link header."""
        if not link_header:
            return None
        
        links = link_header.split(",")
        for link in links:
            if 'rel="next"' in link:
                url = link.split(";")[0].strip(" <>")
                return url
        
        return None
    
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync authentication policies from Okta.
        
        Returns:
            Sync results
        """
        try:
            response = await self.make_request("GET", "/api/v1/policies?type=OKTA_SIGN_ON")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            policies = response.json()
            
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
            logger.error(f"Okta policy sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_policy(self, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process policy data from Okta."""
        try:
            return {
                "external_id": policy_data.get("id"),
                "name": policy_data.get("name"),
                "description": policy_data.get("description"),
                "type": policy_data.get("type"),
                "status": policy_data.get("status"),
                "priority": policy_data.get("priority"),
                "created": policy_data.get("created"),
                "source": "okta",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Okta policy: {e}")
            return None
    
    async def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get groups for a user.
        
        Args:
            user_id: Okta user ID
        
        Returns:
            List of groups
        """
        try:
            response = await self.make_request(
                "GET",
                f"/api/v1/users/{user_id}/groups"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting Okta user groups: {e}")
            return []
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for a user.
        
        Args:
            user_id: Okta user ID
        
        Returns:
            List of active sessions
        """
        try:
            response = await self.make_request(
                "GET",
                f"/api/v1/users/{user_id}/sessions"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting Okta user sessions: {e}")
            return []
    
    async def push_compliance_status(
        self,
        device_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """
        Push compliance status to Okta.
        
        Updates device trust in Okta Verify.
        
        Args:
            device_id: Device identifier
            status: Compliance status
        
        Returns:
            True if successful
        """
        try:
            payload = {
                "deviceId": device_id,
                "trustLevel": "HIGH" if status.get("is_compliant") else "LOW",
                "complianceData": {
                    "compliant": status.get("is_compliant", False),
                    "score": status.get("compliance_score", 0),
                    "violations": status.get("violations", [])
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            response = await self.make_request(
                "PUT",
                f"/api/v1/devices/{device_id}/trust",
                json=payload
            )
            
            return response.status_code in [200, 204]
        
        except Exception as e:
            logger.error(f"Error pushing compliance to Okta: {e}")
            return False
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> bool:
        """
        Push risk score to Okta.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True if successful
        """
        logger.info(f"Risk score for {device_id}: {risk_score.get('total_risk_score')}")
        # Okta doesn't have native risk score API
        # Would use this for conditional access decisions
        return True
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process webhook from Okta.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event
        """
        events = payload.get("data", {}).get("events", [])
        
        processed_events = []
        for event in events:
            event_type = event.get("eventType")
            
            if "user.session" in event_type:
                processed_events.append(self._process_session_event(event))
            elif "user.authentication" in event_type:
                processed_events.append(self._process_auth_event(event))
            elif "device" in event_type:
                processed_events.append(self._process_device_event(event))
            else:
                processed_events.append({
                    "event_type": event_type,
                    "processed": False
                })
        
        return {
            "events_processed": len(processed_events),
            "events": processed_events
        }
    
    def _process_session_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process session event."""
        return {
            "event_type": event.get("eventType"),
            "user_id": event.get("actor", {}).get("id"),
            "user_email": event.get("actor", {}).get("alternateId"),
            "session_id": event.get("authenticationContext", {}).get("externalSessionId"),
            "timestamp": event.get("published"),
            "processed": True
        }
    
    def _process_auth_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process authentication event."""
        return {
            "event_type": event.get("eventType"),
            "user_id": event.get("actor", {}).get("id"),
            "user_email": event.get("actor", {}).get("alternateId"),
            "outcome": event.get("outcome", {}).get("result"),
            "reason": event.get("outcome", {}).get("reason"),
            "ip_address": event.get("client", {}).get("ipAddress"),
            "user_agent": event.get("client", {}).get("userAgent", {}).get("rawUserAgent"),
            "timestamp": event.get("published"),
            "processed": True
        }
    
    def _process_device_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process device event."""
        return {
            "event_type": event.get("eventType"),
            "device_id": event.get("target", [{}])[0].get("id"),
            "user_id": event.get("actor", {}).get("id"),
            "timestamp": event.get("published"),
            "processed": True
        }

