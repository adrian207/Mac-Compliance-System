"""
Munki Integration Connector

Author: Adrian Johnson <adrian207@gmail.com>

Advanced Munki integration for enriched telemetry collection.
"""

import plistlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MunkiConnector:
    """
    Advanced connector for Munki MDM integration.
    
    Provides rich telemetry from Munki's data sources when available.
    """
    
    # Munki file locations
    MANAGED_INSTALL_REPORT = "/Library/Managed Installs/ManagedInstallReport.plist"
    MANAGED_INSTALL_DIR = "/Library/Managed Installs"
    MUNKI_PREFERENCES = "/Library/Preferences/ManagedInstalls.plist"
    
    def __init__(self):
        """Initialize the Munki connector."""
        self.available = self._check_availability()
        self.manifest_data = None
        self.install_report = None
        
        if self.available:
            self._load_data()
    
    def _check_availability(self) -> bool:
        """
        Check if Munki is installed and available.
        
        Returns:
            True if Munki is available, False otherwise
        """
        try:
            # Check for managedsoftwareupdate binary
            result = subprocess.run(
                ["which", "managedsoftwareupdate"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
            
            # Check for managed install report
            return Path(self.MANAGED_INSTALL_REPORT).exists()
            
        except Exception:
            return False
    
    def _load_data(self):
        """Load Munki data from plist files."""
        try:
            # Load managed install report
            if Path(self.MANAGED_INSTALL_REPORT).exists():
                with open(self.MANAGED_INSTALL_REPORT, 'rb') as f:
                    self.install_report = plistlib.load(f)
            
            # Load preferences
            if Path(self.MUNKI_PREFERENCES).exists():
                with open(self.MUNKI_PREFERENCES, 'rb') as f:
                    self.manifest_data = plistlib.load(f)
                    
        except Exception as e:
            print(f"[WARN] Could not load Munki data: {e}")
    
    def get_munki_info(self) -> Dict[str, Any]:
        """
        Get Munki installation and configuration information.
        
        Returns:
            Dict containing Munki info
        """
        if not self.available:
            return {"available": False}
        
        info = {
            "available": True,
            "version": None,
            "client_identifier": None,
            "manifest_name": None,
            "software_repo_url": None,
            "last_check_date": None,
            "last_check_result": None
        }
        
        if self.manifest_data:
            info["client_identifier"] = self.manifest_data.get("ClientIdentifier")
            info["manifest_name"] = self.manifest_data.get("ManifestName")
            info["software_repo_url"] = self.manifest_data.get("SoftwareRepoURL")
        
        if self.install_report:
            info["last_check_date"] = self.install_report.get("StartTime")
            info["last_check_result"] = self.install_report.get("result")
            info["munki_version"] = self.install_report.get("ManagedInstallVersion")
        
        return info
    
    def get_managed_installs(self) -> List[Dict[str, Any]]:
        """
        Get list of Munki-managed software installs.
        
        Returns:
            List of managed install dicts
        """
        if not self.available or not self.install_report:
            return []
        
        installs = []
        managed_items = self.install_report.get("ManagedInstalls", [])
        
        for item in managed_items:
            installs.append({
                "name": item.get("display_name") or item.get("name"),
                "version": item.get("version_to_install") or item.get("installed_version"),
                "installed": item.get("installed", False),
                "unattended": item.get("unattended_install", False)
            })
        
        return installs
    
    def get_optional_installs(self) -> List[str]:
        """
        Get list of optional software available for self-service installation.
        
        Returns:
            List of optional install names
        """
        if not self.available or not self.install_report:
            return []
        
        return self.install_report.get("optional_installs", [])
    
    def get_pending_updates(self) -> Dict[str, Any]:
        """
        Get pending Munki updates.
        
        Returns:
            Dict containing pending update information
        """
        if not self.available or not self.install_report:
            return {"available": False}
        
        updates = {
            "available": True,
            "pending_count": 0,
            "items_to_install": [],
            "items_to_remove": [],
            "apple_updates": []
        }
        
        # Get items to install
        items_to_install = self.install_report.get("ItemsToInstall", [])
        for item in items_to_install:
            updates["items_to_install"].append({
                "name": item.get("display_name") or item.get("name"),
                "version": item.get("version_to_install"),
                "size": item.get("installer_item_size")
            })
        
        # Get items to remove
        items_to_remove = self.install_report.get("ItemsToRemove", [])
        for item in items_to_remove:
            updates["items_to_remove"].append({
                "name": item.get("display_name") or item.get("name"),
                "version": item.get("installed_version")
            })
        
        # Get Apple updates
        apple_updates = self.install_report.get("AppleUpdates", [])
        for update in apple_updates:
            updates["apple_updates"].append({
                "name": update.get("display_name") or update.get("name"),
                "version": update.get("version_to_install"),
                "restart_required": update.get("RestartAction", "None") != "None"
            })
        
        updates["pending_count"] = (
            len(updates["items_to_install"]) +
            len(updates["items_to_remove"]) +
            len(updates["apple_updates"])
        )
        
        return updates
    
    def get_machine_info(self) -> Dict[str, Any]:
        """
        Get machine information from Munki.
        
        Returns:
            Dict containing machine info
        """
        if not self.available or not self.install_report:
            return {}
        
        machine_info = self.install_report.get("MachineInfo", {})
        
        return {
            "hostname": machine_info.get("hostname"),
            "os_version": machine_info.get("os_vers"),
            "os_build": machine_info.get("os_build_number"),
            "machine_model": machine_info.get("machine_model"),
            "architecture": machine_info.get("arch"),
            "serial_number": machine_info.get("serial_number"),
            "physical_memory": machine_info.get("physical_memory"),
            "available_disk_space": machine_info.get("available_disk_space")
        }
    
    def get_install_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent Munki install history.
        
        Args:
            limit: Maximum number of history items to return
        
        Returns:
            List of install history dicts
        """
        if not self.available or not self.install_report:
            return []
        
        history = []
        install_results = self.install_report.get("InstallResults", [])
        
        for result in install_results[:limit]:
            history.append({
                "name": result.get("display_name") or result.get("name"),
                "version": result.get("version"),
                "status": result.get("status"),
                "time": result.get("time")
            })
        
        return history
    
    def get_errors(self) -> List[Dict[str, str]]:
        """
        Get Munki errors from last run.
        
        Returns:
            List of error dicts
        """
        if not self.available or not self.install_report:
            return []
        
        errors = []
        error_list = self.install_report.get("Errors", [])
        
        for error in error_list:
            if isinstance(error, str):
                errors.append({"message": error})
            elif isinstance(error, dict):
                errors.append(error)
        
        return errors
    
    def get_warnings(self) -> List[str]:
        """
        Get Munki warnings from last run.
        
        Returns:
            List of warning strings
        """
        if not self.available or not self.install_report:
            return []
        
        return self.install_report.get("Warnings", [])
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """
        Get Munki compliance status.
        
        Determines if device is compliant with Munki policies.
        
        Returns:
            Dict containing compliance status
        """
        if not self.available or not self.install_report:
            return {
                "compliant": None,
                "reason": "Munki not available"
            }
        
        pending = self.get_pending_updates()
        errors = self.get_errors()
        
        # Device is compliant if:
        # 1. No pending updates
        # 2. No errors
        # 3. Last check was successful
        
        compliant = (
            pending["pending_count"] == 0 and
            len(errors) == 0 and
            self.install_report.get("result") != "error"
        )
        
        reason = []
        if pending["pending_count"] > 0:
            reason.append(f"{pending['pending_count']} pending updates")
        if len(errors) > 0:
            reason.append(f"{len(errors)} errors")
        if self.install_report.get("result") == "error":
            reason.append("Last Munki run failed")
        
        return {
            "compliant": compliant,
            "pending_updates": pending["pending_count"],
            "errors": len(errors),
            "reason": "; ".join(reason) if reason else "Compliant"
        }
    
    def get_full_telemetry(self) -> Dict[str, Any]:
        """
        Get comprehensive Munki telemetry.
        
        Returns:
            Dict containing all available Munki data
        """
        if not self.available:
            return {"munki_available": False}
        
        return {
            "munki_available": True,
            "munki_info": self.get_munki_info(),
            "machine_info": self.get_machine_info(),
            "managed_installs": self.get_managed_installs(),
            "optional_installs": self.get_optional_installs(),
            "pending_updates": self.get_pending_updates(),
            "install_history": self.get_install_history(limit=5),
            "errors": self.get_errors(),
            "warnings": self.get_warnings(),
            "compliance": self.get_compliance_status()
        }

