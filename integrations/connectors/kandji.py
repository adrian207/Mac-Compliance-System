"""
Kandji MDM Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Integrates with Kandji device management platform for Mac endpoint management.
"""

from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
import logging

from integrations.connectors.base import BaseIntegrationConnector
from integrations.models import Integration


logger = logging.getLogger(__name__)


class KandjiConnector(BaseIntegrationConnector):
    """
    Kandji MDM integration connector.
    
    Provides device management, compliance posture, and policy enforcement
    through Kandji's API.
    
    API Documentation: https://api.kandji.io/v1/docs/
    """
    
    def get_integration_type(self) -> str:
        """Get integration type."""
        return "kandji"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get Kandji-specific authentication headers.
        
        Returns:
            Dictionary of headers
        """
        headers = super().get_auth_headers()
        
        # Kandji uses Bearer token authentication
        if self.integration.api_key:
            headers["Authorization"] = f"Bearer {self.integration.api_key}"
        
        return headers
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Kandji API connection.
        
        Returns:
            Connection test results
        """
        try:
            response = await self.make_request("GET", "/api/v1/")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to Kandji",
                    "api_version": "v1"
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed: HTTP {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            logger.error(f"Kandji connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    async def sync_devices(self) -> Dict[str, Any]:
        """
        Sync device data from Kandji.
        
        Retrieves device inventory including hardware details,
        OS version, enrolled status, and compliance state.
        
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
                    f"/api/v1/devices?page={page}&per_page=100"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    devices.extend(data.get("results", []))
                    
                    # Check pagination
                    has_more = data.get("next") is not None
                    page += 1
                else:
                    break
            
            # Process devices
            processed_devices = []
            for device in devices:
                processed = await self._process_device(device)
                if processed:
                    processed_devices.append(processed)
            
            return {
                "success": True,
                "devices_synced": len(processed_devices),
                "devices": processed_devices
            }
        
        except Exception as e:
            logger.error(f"Kandji device sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_device(self, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process device data from Kandji.
        
        Args:
            device_data: Raw device data from Kandji API
        
        Returns:
            Processed device dictionary
        """
        try:
            return {
                "external_id": device_data.get("device_id"),
                "device_name": device_data.get("device_name"),
                "serial_number": device_data.get("serial_number"),
                "model": device_data.get("model"),
                "os_version": device_data.get("os_version"),
                "platform": device_data.get("platform", "macOS"),
                
                # Enrollment status
                "enrolled": device_data.get("is_enrolled", False),
                "enrollment_date": device_data.get("enrollment_date"),
                "last_checkin": device_data.get("last_check_in"),
                
                # User information
                "assigned_user": device_data.get("user", {}).get("name"),
                "user_email": device_data.get("user", {}).get("email"),
                
                # Compliance
                "compliance_status": device_data.get("compliance_status"),
                "blueprint_id": device_data.get("blueprint_id"),
                "blueprint_name": device_data.get("blueprint_name"),
                
                # Hardware
                "hardware_model": device_data.get("model_identifier"),
                "total_ram_gb": device_data.get("total_ram"),
                "storage_capacity_gb": device_data.get("storage_capacity"),
                "storage_available_gb": device_data.get("storage_available"),
                
                # Security
                "filevault_enabled": device_data.get("filevault_enabled"),
                "filevault_status": device_data.get("filevault_status"),
                "gatekeeper_enabled": device_data.get("gatekeeper_enabled"),
                "firewall_enabled": device_data.get("firewall_enabled"),
                "sip_enabled": device_data.get("sip_enabled"),
                
                # Network
                "ip_address": device_data.get("ip_address"),
                "mac_address": device_data.get("mac_address"),
                
                # Agent
                "agent_version": device_data.get("agent_version"),
                
                # Metadata
                "source": "kandji",
                "synced_at": datetime.now(UTC).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error processing Kandji device: {e}")
            return None
    
    async def sync_users(self) -> Dict[str, Any]:
        """
        Sync user data from Kandji.
        
        Returns:
            Sync results
        """
        try:
            users = []
            page = 1
            has_more = True
            
            while has_more:
                response = await self.make_request(
                    "GET",
                    f"/api/v1/users?page={page}&per_page=100"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    users.extend(data.get("results", []))
                    
                    has_more = data.get("next") is not None
                    page += 1
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
            logger.error(f"Kandji user sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process user data from Kandji."""
        try:
            return {
                "external_id": user_data.get("id"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "username": user_data.get("username"),
                "device_count": user_data.get("device_count", 0),
                "source": "kandji",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Kandji user: {e}")
            return None
    
    async def sync_policies(self) -> Dict[str, Any]:
        """
        Sync policy/blueprint data from Kandji.
        
        Returns:
            Sync results
        """
        try:
            response = await self.make_request("GET", "/api/v1/blueprints")
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            blueprints = response.json()
            
            # Process blueprints
            processed_policies = []
            for blueprint in blueprints:
                processed = self._process_blueprint(blueprint)
                if processed:
                    processed_policies.append(processed)
            
            return {
                "success": True,
                "policies_synced": len(processed_policies),
                "policies": processed_policies
            }
        
        except Exception as e:
            logger.error(f"Kandji policy sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_blueprint(self, blueprint_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process blueprint data from Kandji."""
        try:
            return {
                "external_id": blueprint_data.get("id"),
                "name": blueprint_data.get("name"),
                "description": blueprint_data.get("description"),
                "type": "blueprint",
                "device_count": blueprint_data.get("device_count", 0),
                "source": "kandji",
                "synced_at": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing Kandji blueprint: {e}")
            return None
    
    async def get_device_details(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific device.
        
        Args:
            device_id: Kandji device ID
        
        Returns:
            Device details
        """
        try:
            response = await self.make_request(
                "GET",
                f"/api/v1/devices/{device_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting Kandji device details: {e}")
            return None
    
    async def get_device_compliance(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compliance status for a device.
        
        Args:
            device_id: Kandji device ID
        
        Returns:
            Compliance status
        """
        try:
            response = await self.make_request(
                "GET",
                f"/api/v1/devices/{device_id}/status"
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "device_id": device_id,
                    "compliance_status": data.get("compliance_status"),
                    "parameters": data.get("parameters", []),
                    "issues": data.get("issues", [])
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting Kandji device compliance: {e}")
            return None
    
    async def push_compliance_status(
        self,
        device_id: str,
        status: Dict[str, Any]
    ) -> bool:
        """
        Push compliance status to Kandji.
        
        Note: Kandji is primarily a pull-based system. This method logs
        compliance info but doesn't push to Kandji directly.
        
        Args:
            device_id: Device identifier
            status: Compliance status
        
        Returns:
            True if logged successfully
        """
        logger.info(
            f"Compliance status for {device_id}: "
            f"{status.get('is_compliant', 'unknown')}"
        )
        # Kandji doesn't accept external compliance status
        # This would be logged for audit purposes
        return True
    
    async def push_risk_score(
        self,
        device_id: str,
        risk_score: Dict[str, Any]
    ) -> bool:
        """
        Push risk score to Kandji.
        
        Note: Kandji doesn't accept external risk scores via API.
        This logs the information.
        
        Args:
            device_id: Device identifier
            risk_score: Risk score data
        
        Returns:
            True if logged successfully
        """
        logger.info(
            f"Risk score for {device_id}: "
            f"{risk_score.get('total_risk_score', 'unknown')}"
        )
        # Kandji doesn't accept external risk scores
        return True
    
    async def send_remote_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send remote command to device via Kandji.
        
        Args:
            device_id: Kandji device ID
            command: Command to execute
            parameters: Command parameters
        
        Returns:
            Command result
        """
        try:
            payload = {
                "command": command
            }
            
            if parameters:
                payload.update(parameters)
            
            response = await self.make_request(
                "POST",
                f"/api/v1/devices/{device_id}/action",
                json=payload
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    "success": True,
                    "command_id": response.json().get("command_id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"Error sending Kandji remote command: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process webhook from Kandji.
        
        Args:
            payload: Webhook payload
            headers: Request headers
        
        Returns:
            Processed event
        """
        event_type = payload.get("event_type")
        
        if event_type == "device.enrolled":
            return self._process_device_enrolled(payload)
        elif event_type == "device.unenrolled":
            return self._process_device_unenrolled(payload)
        elif event_type == "device.compliance_changed":
            return self._process_compliance_changed(payload)
        elif event_type == "blueprint.assigned":
            return self._process_blueprint_assigned(payload)
        else:
            return {
                "event_type": event_type,
                "processed": False,
                "message": f"Unknown event type: {event_type}"
            }
    
    def _process_device_enrolled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process device enrolled webhook."""
        device = payload.get("device", {})
        
        return {
            "event_type": "device_enrolled",
            "device_id": device.get("device_id"),
            "serial_number": device.get("serial_number"),
            "device_name": device.get("device_name"),
            "user_email": device.get("user", {}).get("email"),
            "enrolled_at": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_device_unenrolled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process device unenrolled webhook."""
        device = payload.get("device", {})
        
        return {
            "event_type": "device_unenrolled",
            "device_id": device.get("device_id"),
            "serial_number": device.get("serial_number"),
            "unenrolled_at": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_compliance_changed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process compliance changed webhook."""
        device = payload.get("device", {})
        
        return {
            "event_type": "compliance_changed",
            "device_id": device.get("device_id"),
            "serial_number": device.get("serial_number"),
            "old_status": payload.get("old_compliance_status"),
            "new_status": payload.get("new_compliance_status"),
            "changed_at": payload.get("timestamp"),
            "processed": True
        }
    
    def _process_blueprint_assigned(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process blueprint assigned webhook."""
        device = payload.get("device", {})
        blueprint = payload.get("blueprint", {})
        
        return {
            "event_type": "blueprint_assigned",
            "device_id": device.get("device_id"),
            "blueprint_id": blueprint.get("id"),
            "blueprint_name": blueprint.get("name"),
            "assigned_at": payload.get("timestamp"),
            "processed": True
        }

