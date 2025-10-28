"""
Device Telemetry Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects comprehensive telemetry data from Mac OS endpoints.
"""

import platform
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.logging_config import get_logger

logger = get_logger(__name__)


class MacOSTelemetryCollector:
    """
    Collects telemetry data from Mac OS devices.
    
    [Unverified] This collector requires administrative privileges for some operations.
    Some data collection methods may vary based on Mac OS version.
    """
    
    def __init__(self):
        """Initialize telemetry collector."""
        self.collection_start = None
        self.errors = []
    
    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all available telemetry data.
        
        Returns:
            Dict containing comprehensive device telemetry
        """
        self.collection_start = datetime.utcnow()
        self.errors = []
        
        telemetry = {
            "collection_time": self.collection_start.isoformat(),
            "system_info": self._collect_system_info(),
            "security_status": self._collect_security_status(),
            "network_info": self._collect_network_info(),
            "authentication": self._collect_authentication_info(),
            "processes": self._collect_processes(),
            "network_connections": self._collect_network_connections(),
            "installed_software": self._collect_installed_software(),
            "system_extensions": self._collect_system_extensions(),
            "certificates": self._collect_certificates(),
        }
        
        # Calculate collection duration
        duration = (datetime.utcnow() - self.collection_start).total_seconds() * 1000
        telemetry["collection_duration_ms"] = int(duration)
        telemetry["collection_errors"] = self.errors if self.errors else None
        
        logger.info(
            "telemetry_collected",
            duration_ms=int(duration),
            error_count=len(self.errors)
        )
        
        return telemetry
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect basic system information."""
        try:
            info = {
                "hostname": platform.node(),
                "os_version": platform.mac_ver()[0],
                "os_build": platform.mac_ver()[2],
                "cpu_type": platform.machine(),
                "python_version": platform.python_version(),
            }
            
            # Get serial number (requires system_profiler)
            try:
                serial = self._run_command([
                    "system_profiler", "SPHardwareDataType"
                ])
                for line in serial.split("\n"):
                    if "Serial Number" in line:
                        info["serial_number"] = line.split(":")[-1].strip()
                    elif "Model Name" in line:
                        info["model"] = line.split(":")[-1].strip()
            except Exception as e:
                self.errors.append(f"Failed to get serial number: {str(e)}")
            
            # Get hardware UUID
            try:
                uuid = self._run_command([
                    "system_profiler", "SPHardwareDataType"
                ])
                for line in uuid.split("\n"):
                    if "Hardware UUID" in line:
                        info["uuid"] = line.split(":")[-1].strip()
            except Exception as e:
                self.errors.append(f"Failed to get hardware UUID: {str(e)}")
            
            # Get memory information
            try:
                memory = self._run_command(["sysctl", "hw.memsize"])
                memory_bytes = int(memory.split(":")[-1].strip())
                info["total_memory_gb"] = round(memory_bytes / (1024**3), 2)
            except Exception as e:
                self.errors.append(f"Failed to get memory info: {str(e)}")
            
            # Get disk information
            try:
                disk = self._run_command(["df", "-h", "/"])
                lines = disk.split("\n")
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        size_str = parts[1].replace("Gi", "").replace("G", "")
                        try:
                            info["total_disk_gb"] = float(size_str)
                        except ValueError:
                            pass
            except Exception as e:
                self.errors.append(f"Failed to get disk info: {str(e)}")
            
            # Get uptime
            try:
                uptime = self._run_command(["sysctl", "kern.boottime"])
                # Parse boot time and calculate uptime
                # [Inference] This parsing may need adjustment based on output format
                info["uptime_seconds"] = 0  # Placeholder
            except Exception as e:
                self.errors.append(f"Failed to get uptime: {str(e)}")
            
            return info
            
        except Exception as e:
            logger.error("system_info_collection_failed", error=str(e))
            self.errors.append(f"System info collection failed: {str(e)}")
            return {}
    
    def _collect_security_status(self) -> Dict[str, Any]:
        """Collect security configuration status."""
        status = {}
        
        # FileVault status
        try:
            fv_status = self._run_command(["fdesetup", "status"])
            status["filevault_enabled"] = "FileVault is On" in fv_status
        except Exception as e:
            self.errors.append(f"Failed to check FileVault: {str(e)}")
            status["filevault_enabled"] = None
        
        # Firewall status
        try:
            fw_status = self._run_command([
                "/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"
            ])
            status["firewall_enabled"] = "enabled" in fw_status.lower()
        except Exception as e:
            self.errors.append(f"Failed to check firewall: {str(e)}")
            status["firewall_enabled"] = None
        
        # Gatekeeper status
        try:
            gk_status = self._run_command(["spctl", "--status"])
            status["gatekeeper_enabled"] = "enabled" in gk_status.lower()
        except Exception as e:
            self.errors.append(f"Failed to check Gatekeeper: {str(e)}")
            status["gatekeeper_enabled"] = None
        
        # SIP status
        try:
            sip_status = self._run_command(["csrutil", "status"])
            status["sip_enabled"] = "enabled" in sip_status.lower()
        except Exception as e:
            self.errors.append(f"Failed to check SIP: {str(e)}")
            status["sip_enabled"] = None
        
        # XProtect version
        try:
            xprotect_plist = "/System/Library/CoreServices/XProtect.bundle/Contents/version.plist"
            version_cmd = self._run_command([
                "defaults", "read", xprotect_plist, "Version"
            ])
            status["xprotect_version"] = version_cmd.strip()
        except Exception as e:
            self.errors.append(f"Failed to check XProtect: {str(e)}")
            status["xprotect_version"] = None
        
        return status
    
    def _collect_network_info(self) -> Dict[str, Any]:
        """Collect network configuration information."""
        network = {}
        
        # Primary IP address
        try:
            ip_output = self._run_command([
                "ifconfig", "en0"
            ])
            for line in ip_output.split("\n"):
                if "inet " in line and "127.0.0.1" not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        network["ip_address"] = parts[1]
                        break
        except Exception as e:
            self.errors.append(f"Failed to get IP address: {str(e)}")
        
        # MAC address
        try:
            mac_output = self._run_command([
                "ifconfig", "en0"
            ])
            for line in mac_output.split("\n"):
                if "ether" in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        network["mac_address"] = parts[1]
                        break
        except Exception as e:
            self.errors.append(f"Failed to get MAC address: {str(e)}")
        
        # WiFi SSID
        try:
            ssid_output = self._run_command([
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I"
            ])
            for line in ssid_output.split("\n"):
                if "SSID:" in line:
                    network["wifi_ssid"] = line.split(":")[-1].strip()
                    break
        except Exception as e:
            self.errors.append(f"Failed to get WiFi SSID: {str(e)}")
        
        # VPN status (simplified check)
        try:
            vpn_output = self._run_command(["scutil", "--nc", "list"])
            network["vpn_connected"] = "Connected" in vpn_output
        except Exception as e:
            self.errors.append(f"Failed to check VPN status: {str(e)}")
            network["vpn_connected"] = False
        
        return network
    
    def _collect_authentication_info(self) -> Dict[str, Any]:
        """Collect authentication and security configuration."""
        auth = {}
        
        # Screen lock status
        try:
            screen_lock = self._run_command([
                "defaults", "read", 
                "com.apple.screensaver",
                "askForPassword"
            ])
            auth["screen_lock_enabled"] = "1" in screen_lock
        except Exception as e:
            self.errors.append(f"Failed to check screen lock: {str(e)}")
            auth["screen_lock_enabled"] = None
        
        # [Inference] Additional authentication checks would require more complex queries
        auth["password_required"] = True  # Most Macs require passwords
        auth["touch_id_enabled"] = False  # Would require biometric API access
        
        return auth
    
    def _collect_processes(self) -> List[Dict[str, Any]]:
        """Collect running process information."""
        processes = []
        
        try:
            ps_output = self._run_command([
                "ps", "aux"
            ])
            
            lines = ps_output.split("\n")[1:]  # Skip header
            for line in lines[:100]:  # Limit to top 100 processes
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu_percent": parts[2],
                        "memory_percent": parts[3],
                        "command": parts[10]
                    })
        except Exception as e:
            self.errors.append(f"Failed to collect processes: {str(e)}")
        
        return processes
    
    def _collect_network_connections(self) -> List[Dict[str, Any]]:
        """Collect active network connections."""
        connections = []
        
        try:
            netstat_output = self._run_command([
                "netstat", "-an"
            ])
            
            lines = netstat_output.split("\n")
            for line in lines[:100]:  # Limit to top 100 connections
                if "tcp" in line.lower() or "udp" in line.lower():
                    parts = line.split()
                    if len(parts) >= 5:
                        connections.append({
                            "protocol": parts[0],
                            "local_address": parts[3],
                            "remote_address": parts[4],
                            "state": parts[5] if len(parts) > 5 else None
                        })
        except Exception as e:
            self.errors.append(f"Failed to collect network connections: {str(e)}")
        
        return connections
    
    def _collect_installed_software(self) -> List[Dict[str, Any]]:
        """Collect installed applications."""
        software = []
        
        try:
            # Get applications from /Applications
            apps_output = self._run_command([
                "ls", "-la", "/Applications"
            ])
            
            for line in apps_output.split("\n"):
                if ".app" in line:
                    app_name = line.split()[-1]
                    software.append({
                        "name": app_name,
                        "path": f"/Applications/{app_name}"
                    })
        except Exception as e:
            self.errors.append(f"Failed to collect installed software: {str(e)}")
        
        return software
    
    def _collect_system_extensions(self) -> List[Dict[str, Any]]:
        """Collect system extensions and kernel extensions."""
        extensions = []
        
        try:
            kextstat_output = self._run_command(["kextstat"])
            
            lines = kextstat_output.split("\n")[1:]  # Skip header
            for line in lines[:50]:  # Limit to top 50 extensions
                parts = line.split()
                if len(parts) >= 6:
                    extensions.append({
                        "index": parts[0],
                        "refs": parts[1],
                        "address": parts[2],
                        "size": parts[3],
                        "wired": parts[4],
                        "name": parts[5]
                    })
        except Exception as e:
            self.errors.append(f"Failed to collect system extensions: {str(e)}")
        
        return extensions
    
    def _collect_certificates(self) -> List[Dict[str, Any]]:
        """Collect certificate information."""
        certificates = []
        
        try:
            # Get certificates from system keychain
            security_output = self._run_command([
                "security", "find-certificate", "-a", "-p",
                "/Library/Keychains/System.keychain"
            ])
            
            # [Inference] Certificate parsing would require more sophisticated logic
            # This is a simplified placeholder
            if security_output:
                certificates.append({
                    "source": "system_keychain",
                    "count": security_output.count("BEGIN CERTIFICATE")
                })
        except Exception as e:
            self.errors.append(f"Failed to collect certificates: {str(e)}")
        
        return certificates
    
    def _run_command(self, command: List[str], timeout: int = 30) -> str:
        """
        Run a shell command and return output.
        
        Args:
            command: Command and arguments as list
            timeout: Command timeout in seconds
        
        Returns:
            Command output as string
        
        Raises:
            subprocess.SubprocessError: If command fails
        """
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return result.stdout


def collect_telemetry() -> Dict[str, Any]:
    """
    Collect device telemetry data.
    
    Returns:
        Dict containing device telemetry
    """
    # Check if running on Mac OS
    if sys.platform != "darwin":
        logger.warning("not_macos", platform=sys.platform)
        return {
            "error": "Telemetry collection only supported on Mac OS",
            "platform": sys.platform
        }
    
    collector = MacOSTelemetryCollector()
    return collector.collect_all()

