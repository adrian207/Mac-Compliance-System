"""
Network Information Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects network configuration and connectivity information.
"""

import re
from typing import Any, Dict, List

from agent.collectors.base import BaseCollector


class NetworkInfoCollector(BaseCollector):
    """
    Collects network configuration and status information.
    
    Gathers data about network interfaces, active connections, VPN status, and DNS configuration.
    """
    
    def _get_active_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get list of active network interfaces.
        
        Returns:
            List of interface dicts
        """
        interfaces = []
        
        try:
            output = self._execute_command(["ifconfig"])
            
            # Parse ifconfig output
            current_interface = None
            for line in output.split('\n'):
                if not line.startswith('\t') and not line.startswith(' '):
                    # New interface
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    interface_name = line.split(':')[0]
                    current_interface = {
                        "name": interface_name,
                        "status": "up" if "UP" in line else "down"
                    }
                elif current_interface:
                    # Parse interface details
                    if "inet " in line:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            current_interface["ip_address"] = ip_match.group(1)
                    
                    if "ether " in line:
                        mac_match = re.search(r'ether ([0-9a-f:]+)', line)
                        if mac_match:
                            current_interface["mac_address"] = mac_match.group(1)
            
            # Add last interface
            if current_interface:
                interfaces.append(current_interface)
            
        except Exception as e:
            print(f"[WARN] Could not get network interfaces: {e}")
        
        return interfaces
    
    def _get_primary_interface(self) -> Dict[str, Any]:
        """
        Get the primary network interface.
        
        Returns:
            Primary interface info dict
        """
        try:
            # Get default route
            output = self._execute_command(["route", "-n", "get", "default"])
            
            interface_match = re.search(r'interface: (\w+)', output)
            gateway_match = re.search(r'gateway: ([\d.]+)', output)
            
            interface_name = interface_match.group(1) if interface_match else None
            gateway = gateway_match.group(1) if gateway_match else None
            
            return {
                "interface": interface_name,
                "gateway": gateway
            }
        except Exception as e:
            print(f"[WARN] Could not get primary interface: {e}")
            return {}
    
    def _get_dns_config(self) -> Dict[str, Any]:
        """
        Get DNS configuration.
        
        Returns:
            DNS config dict
        """
        try:
            output = self._execute_command(["scutil", "--dns"])
            
            # Parse DNS servers
            dns_servers = []
            for line in output.split('\n'):
                if "nameserver" in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        dns_servers.append(parts[1].strip())
            
            # Get search domains
            search_domains = []
            for line in output.split('\n'):
                if "search domain" in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        search_domains.append(parts[1].strip())
            
            return {
                "dns_servers": list(set(dns_servers)),  # Remove duplicates
                "search_domains": list(set(search_domains))
            }
        except Exception as e:
            print(f"[WARN] Could not get DNS config: {e}")
            return {}
    
    def _check_vpn_connections(self) -> Dict[str, Any]:
        """
        Check for active VPN connections.
        
        Returns:
            VPN status dict
        """
        try:
            # Check scutil for VPN interfaces
            output = self._execute_command(["scutil", "--nc", "list"])
            
            vpn_connections = []
            for line in output.split('\n'):
                if "Connected" in line or "Connecting" in line:
                    # Parse VPN name and status
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        vpn_connections.append({
                            "name": ' '.join(parts[2:-1]) if len(parts) > 3 else parts[1],
                            "status": parts[-1].strip('()')
                        })
            
            return {
                "active_vpns": vpn_connections,
                "vpn_active": len(vpn_connections) > 0
            }
        except Exception as e:
            print(f"[WARN] Could not check VPN status: {e}")
            return {"vpn_active": False}
    
    def _check_proxy_settings(self) -> Dict[str, Any]:
        """
        Check proxy configuration.
        
        Returns:
            Proxy config dict
        """
        try:
            output = self._execute_command(["scutil", "--proxy"])
            
            http_proxy = None
            https_proxy = None
            pac_url = None
            
            for line in output.split('\n'):
                if "HTTPProxy" in line and ":" in line:
                    http_proxy = line.split(':')[1].strip()
                elif "HTTPSProxy" in line and ":" in line:
                    https_proxy = line.split(':')[1].strip()
                elif "ProxyAutoConfigURLString" in line and ":" in line:
                    pac_url = line.split(':')[1].strip()
            
            return {
                "http_proxy": http_proxy,
                "https_proxy": https_proxy,
                "pac_url": pac_url,
                "proxy_enabled": any([http_proxy, https_proxy, pac_url])
            }
        except Exception as e:
            print(f"[WARN] Could not check proxy settings: {e}")
            return {"proxy_enabled": False}
    
    def _check_wifi_info(self) -> Dict[str, Any]:
        """
        Get current Wi-Fi information.
        
        Returns:
            Wi-Fi info dict
        """
        try:
            # Get current Wi-Fi network
            output = self._execute_command([
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I"
            ])
            
            ssid = None
            bssid = None
            security = None
            
            for line in output.split('\n'):
                if " SSID:" in line:
                    ssid = line.split(':')[1].strip()
                elif "BSSID:" in line:
                    bssid = line.split(':')[1].strip()
                elif "link auth:" in line:
                    security = line.split(':')[1].strip()
            
            return {
                "connected": ssid is not None,
                "ssid": ssid,
                "bssid": bssid,
                "security": security
            }
        except Exception as e:
            print(f"[WARN] Could not get Wi-Fi info: {e}")
            return {"connected": False}
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect network information.
        
        Returns:
            Dict containing comprehensive network information
        """
        network_info = {
            "network_info": {
                "interfaces": self._get_active_interfaces(),
                "primary_interface": self._get_primary_interface(),
                "dns": self._get_dns_config(),
                "vpn": self._check_vpn_connections(),
                "proxy": self._check_proxy_settings(),
                "wifi": self._check_wifi_info()
            }
        }
        
        return network_info

