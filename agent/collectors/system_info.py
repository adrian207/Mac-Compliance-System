"""
System Information Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects hardware and OS information from Mac OS devices.
Can leverage Munki data when available or collect directly.
"""

import platform
import subprocess
from typing import Any, Dict, Optional

from agent.collectors.base import BaseCollector


class SystemInfoCollector(BaseCollector):
    """
    Collects system hardware and OS information.
    
    Supports hybrid mode: uses Munki data if available, falls back to direct collection.
    """
    
    def __init__(self):
        """Initialize the system info collector."""
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
    
    def _get_munki_system_info(self) -> Optional[Dict[str, Any]]:
        """
        Get system info from Munki's managed installs plist.
        
        Returns:
            System info dict if available, None otherwise
        """
        if not self.munki_available:
            return None
        
        try:
            import plistlib
            munki_plist = "/Library/Managed Installs/ManagedInstallReport.plist"
            
            with open(munki_plist, 'rb') as f:
                data = plistlib.load(f)
            
            # Extract relevant system info
            return {
                "machine_info": data.get("MachineInfo", {}),
                "munki_version": data.get("ManifestName"),
                "last_munki_run": data.get("EndTime")
            }
        except Exception as e:
            print(f"[WARN] Could not read Munki data: {e}")
            return None
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """
        Get hardware information directly from system_profiler.
        
        Returns:
            Hardware info dict
        """
        try:
            data = self._parse_system_profiler("SPHardwareDataType")
            
            # Extract hardware data
            if data and len(data) > 0 and "_items" in data[0]:
                hw_items = data[0]["_items"][0]
                
                return {
                    "model": hw_items.get("machine_model"),
                    "model_name": hw_items.get("machine_name"),
                    "serial_number": hw_items.get("serial_number"),
                    "processor": hw_items.get("chip_type") or hw_items.get("cpu_type"),
                    "processor_cores": hw_items.get("number_processors"),
                    "memory_gb": int(hw_items.get("physical_memory", "0 GB").split()[0]),
                    "boot_rom_version": hw_items.get("boot_rom_version"),
                    "smc_version": hw_items.get("SMC_version_system")
                }
        except Exception as e:
            print(f"[WARN] Could not get hardware info: {e}")
        
        return {}
    
    def _get_os_info(self) -> Dict[str, Any]:
        """
        Get operating system information.
        
        Returns:
            OS info dict
        """
        try:
            os_version = platform.mac_ver()[0]
            build_version = self._execute_command(["sw_vers", "-buildVersion"])
            
            # Get macOS version name
            version_parts = os_version.split('.')
            major = int(version_parts[0]) if version_parts else 0
            
            # macOS version mapping
            version_names = {
                15: "Sequoia",
                14: "Sonoma",
                13: "Ventura",
                12: "Monterey",
                11: "Big Sur",
                10: "Catalina/Mojave/High Sierra/Sierra"
            }
            
            version_name = version_names.get(major, "Unknown")
            
            return {
                "os_version": os_version,
                "os_build": build_version,
                "os_name": f"macOS {version_name}",
                "kernel_version": platform.release(),
                "architecture": platform.machine()
            }
        except Exception as e:
            print(f"[WARN] Could not get OS info: {e}")
            return {
                "os_version": platform.mac_ver()[0],
                "architecture": platform.machine()
            }
    
    def _get_uptime(self) -> Dict[str, Any]:
        """
        Get system uptime information.
        
        Returns:
            Uptime info dict
        """
        try:
            uptime_output = self._execute_command(["uptime"])
            boot_time = self._execute_command(["sysctl", "-n", "kern.boottime"])
            
            return {
                "uptime": uptime_output,
                "boot_time": boot_time
            }
        except Exception as e:
            print(f"[WARN] Could not get uptime: {e}")
            return {}
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect system information.
        
        Uses Munki data if available, falls back to direct collection.
        
        Returns:
            Dict containing system information
        """
        system_info = {
            "system_info": {
                "collection_method": "munki" if self.munki_available else "direct",
                "munki_installed": self.munki_available
            }
        }
        
        # Try Munki first
        munki_data = self._get_munki_system_info()
        if munki_data and munki_data.get("machine_info"):
            machine_info = munki_data["machine_info"]
            
            system_info["system_info"].update({
                "hardware": {
                    "model": machine_info.get("machine_model"),
                    "serial_number": machine_info.get("serial_number"),
                    "processor": machine_info.get("arch"),
                    "memory_gb": machine_info.get("physical_memory") // 1024 if machine_info.get("physical_memory") else None
                },
                "os": {
                    "os_version": machine_info.get("os_vers"),
                    "os_build": machine_info.get("os_build_number"),
                    "architecture": machine_info.get("arch")
                },
                "munki_info": {
                    "manifest": munki_data.get("munki_version"),
                    "last_run": munki_data.get("last_munki_run")
                }
            })
        else:
            # Fall back to direct collection
            system_info["system_info"]["hardware"] = self._get_hardware_info()
            system_info["system_info"]["os"] = self._get_os_info()
        
        # Always collect uptime directly (Munki doesn't track this)
        system_info["system_info"]["uptime"] = self._get_uptime()
        
        return system_info

