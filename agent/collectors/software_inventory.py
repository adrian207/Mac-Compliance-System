"""
Software Inventory Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects installed software inventory.
Leverages Munki data when available, falls back to system_profiler.
"""

import subprocess
from typing import Any, Dict, List, Optional

from agent.collectors.base import BaseCollector


class SoftwareInventoryCollector(BaseCollector):
    """
    Collects software inventory from the device.
    
    Uses Munki data for efficiency when available, otherwise uses system_profiler.
    """
    
    def __init__(self):
        """Initialize the software inventory collector."""
        super().__init__()
        self.munki_available = self._check_munki_available()
    
    def _check_munki_available(self) -> bool:
        """
        Check if Munki is installed and available.
        
        Returns:
            True if Munki is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["which", "managedsoftwareupdate"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_munki_inventory(self) -> Optional[Dict[str, Any]]:
        """
        Get software inventory from Munki.
        
        Returns:
            Software inventory dict from Munki, or None if unavailable
        """
        if not self.munki_available:
            return None
        
        try:
            import plistlib
            
            # Read Munki's managed installs report
            munki_plist = "/Library/Managed Installs/ManagedInstallReport.plist"
            
            with open(munki_plist, 'rb') as f:
                data = plistlib.load(f)
            
            # Extract installed items
            managed_items = data.get("ManagedInstalls", [])
            optional_items = data.get("InstalledItems", [])
            
            all_items = []
            
            # Process managed installs
            for item in managed_items:
                all_items.append({
                    "name": item.get("display_name") or item.get("name"),
                    "version": item.get("version_to_install") or item.get("installed_version"),
                    "managed": True,
                    "source": "munki"
                })
            
            # Process optional installs
            for item in optional_items:
                if item not in [i["name"] for i in all_items]:  # Avoid duplicates
                    all_items.append({
                        "name": item,
                        "managed": False,
                        "source": "munki"
                    })
            
            return {
                "method": "munki",
                "items": all_items,
                "total_count": len(all_items),
                "managed_count": len(managed_items),
                "last_munki_run": data.get("EndTime")
            }
            
        except Exception as e:
            print(f"[WARN] Could not read Munki inventory: {e}")
            return None
    
    def _get_system_profiler_inventory(self) -> Dict[str, Any]:
        """
        Get software inventory using system_profiler.
        
        Returns:
            Software inventory dict from system_profiler
        """
        items = []
        
        try:
            data = self._parse_system_profiler("SPApplicationsDataType")
            
            if data and len(data) > 0 and "_items" in data[0]:
                for app in data[0]["_items"]:
                    # Filter to major applications
                    app_name = app.get("_name")
                    version = app.get("version")
                    
                    if app_name and version:
                        items.append({
                            "name": app_name,
                            "version": version,
                            "obtained_from": app.get("obtained_from"),
                            "last_modified": app.get("lastModified"),
                            "source": "system_profiler"
                        })
            
            return {
                "method": "system_profiler",
                "items": items[:100],  # Limit to 100 applications
                "total_count": len(items),
                "note": "Limited to first 100 applications" if len(items) > 100 else None
            }
            
        except Exception as e:
            print(f"[WARN] Could not get system_profiler inventory: {e}")
            return {
                "method": "system_profiler",
                "items": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def _get_homebrew_packages(self) -> List[Dict[str, str]]:
        """
        Get installed Homebrew packages if available.
        
        Returns:
            List of Homebrew packages
        """
        packages = []
        
        try:
            # Check if brew is installed
            result = subprocess.run(
                ["which", "brew"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Get list of installed packages
                output = self._execute_command(["brew", "list", "--versions"])
                
                for line in output.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            packages.append({
                                "name": parts[0],
                                "version": ' '.join(parts[1:]),
                                "source": "homebrew"
                            })
        except Exception as e:
            print(f"[WARN] Could not get Homebrew packages: {e}")
        
        return packages
    
    def _check_critical_software(self, inventory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for presence of critical security and productivity software.
        
        Args:
            inventory: Software inventory dict
        
        Returns:
            Dict of critical software status
        """
        items = inventory.get("items", [])
        item_names = [item["name"].lower() for item in items]
        
        critical_software = {
            "browsers": {
                "chrome": any("chrome" in name for name in item_names),
                "firefox": any("firefox" in name for name in item_names),
                "safari": any("safari" in name for name in item_names),
                "edge": any("edge" in name for name in item_names)
            },
            "security": {
                "antivirus": any(av in ' '.join(item_names) for av in ["crowdstrike", "sentinel", "sophos", "malwarebytes"]),
                "vpn": any(vpn in ' '.join(item_names) for vpn in ["zscaler", "globalprotect", "cisco anyconnect", "openvpn"]),
                "password_manager": any(pm in ' '.join(item_names) for pm in ["1password", "lastpass", "dashlane", "bitwarden"])
            },
            "productivity": {
                "office": any(office in ' '.join(item_names) for office in ["microsoft office", "microsoft word", "microsoft excel"]),
                "slack": any("slack" in name for name in item_names),
                "zoom": any("zoom" in name for name in item_names),
                "teams": any("teams" in name for name in item_names)
            }
        }
        
        return critical_software
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect software inventory.
        
        Uses Munki if available, falls back to system_profiler.
        
        Returns:
            Dict containing software inventory
        """
        # Try Munki first
        inventory = self._get_munki_inventory()
        
        # Fall back to system_profiler if Munki unavailable
        if not inventory:
            inventory = self._get_system_profiler_inventory()
        
        # Add Homebrew packages if available
        homebrew_packages = self._get_homebrew_packages()
        if homebrew_packages:
            inventory["homebrew_packages"] = homebrew_packages
            inventory["homebrew_count"] = len(homebrew_packages)
        
        # Check for critical software
        critical_software = self._check_critical_software(inventory)
        
        software_inventory = {
            "software_inventory": {
                **inventory,
                "critical_software": critical_software,
                "munki_available": self.munki_available
            }
        }
        
        return software_inventory

