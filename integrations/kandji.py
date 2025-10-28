"""
Kandji MDM Integration

Author: Adrian Johnson <adrian207@gmail.com>

Integration with Kandji endpoint management platform for device management,
policy deployment, and compliance enforcement.
"""

from typing import Any, Dict, List, Optional

from integrations.base import BaseIntegration
from core.config import get_config
from core.logging_config import get_logger

logger = get_logger(__name__)


class KandjiIntegration(BaseIntegration):
    """
    Kandji MDM platform integration.
    
    Provides functionality for:
    - Device enrollment and inventory
    - Policy and configuration deployment
    - Compliance checking and remediation
    - Software distribution and updates
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize Kandji integration.
        
        Args:
            config: Optional KandjiConfig object. If None, loads from global config.
        """
        if config is None:
            global_config = get_config()
            config = global_config.kandji
        
        if not config or not config.enabled:
            raise ValueError("Kandji integration is not enabled")
        
        super().__init__(
            api_url=config.api_url,
            timeout=config.timeout_seconds,
            retry_attempts=config.retry_attempts
        )
        
        self.api_token = config.api_token
        self.tenant_id = config.tenant_id
        self.auto_deploy_policies = config.auto_deploy_policies
        self.auto_remediate_compliance = config.auto_remediate_compliance
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Kandji API."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to Kandji API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.get("/devices", params={"limit": 1})
            logger.info("kandji_connection_successful")
            return True
        except Exception as e:
            logger.error("kandji_connection_failed", error=str(e))
            return False
    
    def get_devices(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of managed devices.
        
        Args:
            limit: Maximum number of devices to return
            offset: Pagination offset
            filters: Optional filters for device query
        
        Returns:
            List of device objects
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            params.update(filters)
        
        try:
            response = self.get("/devices", params=params)
            devices = response.get("results", [])
            
            logger.info(
                "kandji_devices_retrieved",
                count=len(devices)
            )
            
            return devices
        except Exception as e:
            logger.error("kandji_devices_retrieval_failed", error=str(e))
            return []
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific device.
        
        Args:
            device_id: Kandji device ID
        
        Returns:
            Device object or None if not found
        """
        try:
            device = self.get(f"/devices/{device_id}")
            logger.info("kandji_device_retrieved", device_id=device_id)
            return device
        except Exception as e:
            logger.error(
                "kandji_device_retrieval_failed",
                device_id=device_id,
                error=str(e)
            )
            return None
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device status and compliance information.
        
        Args:
            device_id: Kandji device ID
        
        Returns:
            Device status object or None
        """
        try:
            status = self.get(f"/devices/{device_id}/status")
            logger.info("kandji_device_status_retrieved", device_id=device_id)
            return status
        except Exception as e:
            logger.error(
                "kandji_device_status_retrieval_failed",
                device_id=device_id,
                error=str(e)
            )
            return None
    
    def deploy_policy(
        self,
        device_id: str,
        policy_id: str
    ) -> bool:
        """
        Deploy a policy to a device.
        
        Args:
            device_id: Kandji device ID
            policy_id: Kandji policy/blueprint ID
        
        Returns:
            True if deployment initiated, False otherwise
        """
        try:
            response = self.post(
                f"/devices/{device_id}/actions/install",
                data={"policy_id": policy_id}
            )
            
            logger.info(
                "kandji_policy_deployed",
                device_id=device_id,
                policy_id=policy_id
            )
            
            return response.get("success", False)
        except Exception as e:
            logger.error(
                "kandji_policy_deployment_failed",
                device_id=device_id,
                policy_id=policy_id,
                error=str(e)
            )
            return False
    
    def remediate_device(
        self,
        device_id: str,
        remediation_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Execute remediation actions on a device.
        
        Args:
            device_id: Kandji device ID
            remediation_actions: List of remediation action IDs
        
        Returns:
            Dict with remediation results
        """
        results = {
            "device_id": device_id,
            "actions": [],
            "success": True
        }
        
        for action in remediation_actions:
            try:
                response = self.post(
                    f"/devices/{device_id}/actions/{action}",
                    data={}
                )
                
                results["actions"].append({
                    "action": action,
                    "status": "success",
                    "response": response
                })
                
                logger.info(
                    "kandji_remediation_action_executed",
                    device_id=device_id,
                    action=action
                )
            
            except Exception as e:
                results["success"] = False
                results["actions"].append({
                    "action": action,
                    "status": "failed",
                    "error": str(e)
                })
                
                logger.error(
                    "kandji_remediation_action_failed",
                    device_id=device_id,
                    action=action,
                    error=str(e)
                )
        
        return results
    
    def lock_device(self, device_id: str, message: Optional[str] = None) -> bool:
        """
        Remotely lock a device.
        
        Args:
            device_id: Kandji device ID
            message: Optional message to display on locked device
        
        Returns:
            True if lock command sent, False otherwise
        """
        try:
            data = {}
            if message:
                data["message"] = message
            
            response = self.post(
                f"/devices/{device_id}/actions/lock",
                data=data
            )
            
            logger.info("kandji_device_locked", device_id=device_id)
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "kandji_device_lock_failed",
                device_id=device_id,
                error=str(e)
            )
            return False
    
    def wipe_device(
        self,
        device_id: str,
        wipe_type: str = "remote_wipe"
    ) -> bool:
        """
        Remotely wipe a device.
        
        [Unverified] This is a destructive action that will erase device data.
        Use with extreme caution.
        
        Args:
            device_id: Kandji device ID
            wipe_type: Type of wipe (remote_wipe, erase_device)
        
        Returns:
            True if wipe command sent, False otherwise
        """
        try:
            response = self.post(
                f"/devices/{device_id}/actions/{wipe_type}",
                data={}
            )
            
            logger.warning(
                "kandji_device_wipe_initiated",
                device_id=device_id,
                wipe_type=wipe_type
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "kandji_device_wipe_failed",
                device_id=device_id,
                error=str(e)
            )
            return False
    
    def get_installed_software(
        self,
        device_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get installed software inventory for a device.
        
        Args:
            device_id: Kandji device ID
        
        Returns:
            List of installed software
        """
        try:
            response = self.get(f"/devices/{device_id}/apps")
            apps = response.get("results", [])
            
            logger.info(
                "kandji_software_inventory_retrieved",
                device_id=device_id,
                app_count=len(apps)
            )
            
            return apps
        
        except Exception as e:
            logger.error(
                "kandji_software_inventory_failed",
                device_id=device_id,
                error=str(e)
            )
            return []
    
    def install_software(
        self,
        device_id: str,
        app_id: str
    ) -> bool:
        """
        Install software on a device.
        
        Args:
            device_id: Kandji device ID
            app_id: Kandji application ID
        
        Returns:
            True if installation initiated, False otherwise
        """
        try:
            response = self.post(
                f"/devices/{device_id}/apps/{app_id}/install",
                data={}
            )
            
            logger.info(
                "kandji_software_installation_initiated",
                device_id=device_id,
                app_id=app_id
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "kandji_software_installation_failed",
                device_id=device_id,
                app_id=app_id,
                error=str(e)
            )
            return False
    
    def update_device_attributes(
        self,
        device_id: str,
        attributes: Dict[str, Any]
    ) -> bool:
        """
        Update device attributes and metadata.
        
        Args:
            device_id: Kandji device ID
            attributes: Dict of attributes to update
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            response = self.put(
                f"/devices/{device_id}",
                data=attributes
            )
            
            logger.info(
                "kandji_device_attributes_updated",
                device_id=device_id
            )
            
            return response.get("success", False)
        
        except Exception as e:
            logger.error(
                "kandji_device_attributes_update_failed",
                device_id=device_id,
                error=str(e)
            )
            return False


def get_kandji_client() -> KandjiIntegration:
    """
    Get configured Kandji integration client.
    
    Returns:
        KandjiIntegration instance
    """
    return KandjiIntegration()

