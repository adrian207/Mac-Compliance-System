"""
Security Status Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects security posture information from Mac OS devices.
Monitors FileVault, SIP, Firewall, Gatekeeper, and other security features.
"""

import re
from typing import Any, Dict

from agent.collectors.base import BaseCollector


class SecurityStatusCollector(BaseCollector):
    """
    Collects device security status and configuration.
    
    Monitors all key security features that contribute to device risk score.
    """
    
    def _check_filevault(self) -> Dict[str, Any]:
        """
        Check FileVault encryption status.
        
        Returns:
            FileVault status dict
        """
        try:
            output = self._execute_command(["fdesetup", "status"])
            
            enabled = "FileVault is On" in output or "Encryption in progress" in output
            encrypting = "Encryption in progress" in output
            
            return {
                "enabled": enabled,
                "encrypting": encrypting,
                "status": output.strip()
            }
        except Exception as e:
            print(f"[WARN] Could not check FileVault: {e}")
            return {"enabled": False, "error": str(e)}
    
    def _check_sip(self) -> Dict[str, Any]:
        """
        Check System Integrity Protection status.
        
        Returns:
            SIP status dict
        """
        try:
            output = self._execute_command(["csrutil", "status"])
            enabled = "enabled" in output.lower()
            
            return {
                "enabled": enabled,
                "status": output.strip()
            }
        except Exception as e:
            print(f"[WARN] Could not check SIP: {e}")
            return {"enabled": None, "error": str(e)}
    
    def _check_firewall(self) -> Dict[str, Any]:
        """
        Check firewall status.
        
        Returns:
            Firewall status dict
        """
        try:
            # Check if firewall is enabled
            output = self._execute_command([
                "/usr/libexec/ApplicationFirewall/socketfilterfw",
                "--getglobalstate"
            ])
            
            enabled = "enabled" in output.lower()
            
            # Get stealth mode status
            try:
                stealth_output = self._execute_command([
                    "/usr/libexec/ApplicationFirewall/socketfilterfw",
                    "--getstealthmode"
                ])
                stealth_mode = "enabled" in stealth_output.lower()
            except Exception:
                stealth_mode = None
            
            return {
                "enabled": enabled,
                "stealth_mode": stealth_mode,
                "status": output.strip()
            }
        except Exception as e:
            print(f"[WARN] Could not check firewall: {e}")
            return {"enabled": False, "error": str(e)}
    
    def _check_gatekeeper(self) -> Dict[str, Any]:
        """
        Check Gatekeeper status.
        
        Returns:
            Gatekeeper status dict
        """
        try:
            output = self._execute_command(["spctl", "--status"])
            enabled = "assessments enabled" in output.lower()
            
            return {
                "enabled": enabled,
                "status": output.strip()
            }
        except Exception as e:
            print(f"[WARN] Could not check Gatekeeper: {e}")
            return {"enabled": None, "error": str(e)}
    
    def _check_xprotect(self) -> Dict[str, Any]:
        """
        Check XProtect (built-in malware protection) version.
        
        Returns:
            XProtect info dict
        """
        try:
            # Check XProtect version from system profiler
            data = self._parse_system_profiler("SPInstallHistoryDataType")
            
            xprotect_version = None
            xprotect_date = None
            
            if data and len(data) > 0 and "_items" in data[0]:
                for item in data[0]["_items"]:
                    display_name = item.get("_name", "")
                    if "XProtect" in display_name:
                        xprotect_version = item.get("version")
                        xprotect_date = item.get("install_date")
                        break
            
            return {
                "version": xprotect_version,
                "last_update": xprotect_date,
                "enabled": True  # XProtect is always enabled on modern macOS
            }
        except Exception as e:
            print(f"[WARN] Could not check XProtect: {e}")
            return {"enabled": True, "error": str(e)}
    
    def _check_secure_boot(self) -> Dict[str, Any]:
        """
        Check Secure Boot status (Apple Silicon only).
        
        Returns:
            Secure Boot status dict
        """
        try:
            import platform
            arch = platform.machine()
            
            if arch not in ["arm64", "arm64e"]:
                return {
                    "supported": False,
                    "reason": "Intel Mac - not applicable"
                }
            
            # For Apple Silicon Macs
            output = self._execute_command(["nvram", "94b73556-2197-4702-82a8-3e1337dafbfb:AppleSecureBootPolicy"])
            
            # Parse secure boot level
            # 0 = Permissive, 1 = Reduced, 2 = Full
            if "02" in output or "2" in output:
                level = "full"
            elif "01" in output or "1" in output:
                level = "reduced"
            else:
                level = "permissive"
            
            return {
                "supported": True,
                "level": level,
                "secure": level == "full"
            }
        except Exception as e:
            # Command fails on Intel Macs
            import platform
            if platform.machine() in ["arm64", "arm64e"]:
                print(f"[WARN] Could not check Secure Boot: {e}")
                return {"supported": True, "error": str(e)}
            else:
                return {"supported": False, "reason": "Intel Mac"}
    
    def _check_remote_desktop(self) -> Dict[str, Any]:
        """
        Check if Screen Sharing (Remote Desktop) is enabled.
        
        Returns:
            Remote desktop status dict
        """
        try:
            output = self._execute_command([
                "sudo",
                "launchctl",
                "list"
            ])
            
            screen_sharing_enabled = "com.apple.screensharing" in output
            
            return {
                "enabled": screen_sharing_enabled,
                "risk": "high" if screen_sharing_enabled else "none"
            }
        except Exception:
            # If we can't check (likely no sudo), assume disabled
            return {"enabled": False, "check_failed": True}
    
    def _check_ssh(self) -> Dict[str, Any]:
        """
        Check if SSH (Remote Login) is enabled.
        
        Returns:
            SSH status dict
        """
        try:
            output = self._execute_command(["systemsetup", "-getremotelogin"])
            enabled = "On" in output
            
            return {
                "enabled": enabled,
                "risk": "medium" if enabled else "none"
            }
        except Exception as e:
            print(f"[WARN] Could not check SSH: {e}")
            return {"enabled": None, "error": str(e)}
    
    def _check_auto_login(self) -> Dict[str, Any]:
        """
        Check if automatic login is enabled.
        
        Returns:
            Auto-login status dict
        """
        try:
            output = self._execute_command(["defaults", "read", "/Library/Preferences/com.apple.loginwindow", "autoLoginUser"])
            
            # If the command succeeds and returns a username, auto-login is enabled
            enabled = len(output.strip()) > 0 and "does not exist" not in output.lower()
            auto_login_user = output.strip() if enabled else None
            
            return {
                "enabled": enabled,
                "user": auto_login_user,
                "risk": "critical" if enabled else "none"
            }
        except Exception:
            # Key doesn't exist = auto-login disabled
            return {"enabled": False, "risk": "none"}
    
    def _check_password_requirements(self) -> Dict[str, Any]:
        """
        Check password policy requirements.
        
        Returns:
            Password policy dict
        """
        try:
            # Check password complexity requirements
            output = self._execute_command(["pwpolicy", "-getaccountpolicies"])
            
            # Parse policy XML/plist
            requires_complex = "requiresAlpha" in output or "requiresNumeric" in output
            min_length_match = re.search(r'policyAttributePassword matches.*minLength=(\d+)', output)
            min_length = int(min_length_match.group(1)) if min_length_match else None
            
            return {
                "requires_complex": requires_complex,
                "min_length": min_length,
                "policy_enforced": len(output.strip()) > 0
            }
        except Exception as e:
            print(f"[WARN] Could not check password policy: {e}")
            return {"policy_enforced": False, "error": str(e)}
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect all security status information.
        
        Returns:
            Dict containing comprehensive security status
        """
        security_status = {
            "security_status": {
                "filevault": self._check_filevault(),
                "sip": self._check_sip(),
                "firewall": self._check_firewall(),
                "gatekeeper": self._check_gatekeeper(),
                "xprotect": self._check_xprotect(),
                "secure_boot": self._check_secure_boot(),
                "remote_access": {
                    "screen_sharing": self._check_remote_desktop(),
                    "ssh": self._check_ssh()
                },
                "authentication": {
                    "auto_login": self._check_auto_login(),
                    "password_policy": self._check_password_requirements()
                }
            }
        }
        
        return security_status

