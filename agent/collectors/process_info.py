"""
Process Information Collector

Author: Adrian Johnson <adrian207@gmail.com>

Collects information about running processes and services.
"""

import re
from typing import Any, Dict, List

from agent.collectors.base import BaseCollector


class ProcessInfoCollector(BaseCollector):
    """
    Collects information about running processes and system services.
    
    Monitors security-relevant processes and services.
    """
    
    # Security-relevant processes to monitor
    SECURITY_PROCESSES = [
        "CrowdStrike",
        "SentinelAgent",
        "osqueryd",
        "Little Snitch",
        "Lulu",
        "BlockBlock",
        "KnockKnock",
        "ReiKey",
        "OverSight",
        "Do Not Disturb",
        "Santa",
        "Zscaler",
        "GlobalProtect",
        "Cisco AnyConnect"
    ]
    
    def _get_running_security_tools(self) -> List[Dict[str, str]]:
        """
        Check for running security tools.
        
        Returns:
            List of detected security tools
        """
        detected_tools = []
        
        try:
            output = self._execute_command(["ps", "aux"])
            
            for tool in self.SECURITY_PROCESSES:
                if tool.lower() in output.lower():
                    # Find the process line
                    for line in output.split('\n'):
                        if tool.lower() in line.lower():
                            parts = line.split()
                            if len(parts) > 10:
                                detected_tools.append({
                                    "name": tool,
                                    "process": ' '.join(parts[10:]),
                                    "pid": parts[1],
                                    "cpu": parts[2],
                                    "memory": parts[3]
                                })
                            break
        except Exception as e:
            print(f"[WARN] Could not check security processes: {e}")
        
        return detected_tools
    
    def _get_launch_agents(self) -> Dict[str, Any]:
        """
        Get information about launch agents and daemons.
        
        Returns:
            Launch agents/daemons info
        """
        agents_info = {
            "user_agents": [],
            "system_agents": [],
            "daemons": []
        }
        
        try:
            # Get user launch agents
            output = self._execute_command(["launchctl", "list"])
            
            # Parse launchctl list output
            agent_count = 0
            for line in output.split('\n')[1:]:  # Skip header
                if line.strip():
                    agent_count += 1
            
            agents_info["user_agent_count"] = agent_count
            
        except Exception as e:
            print(f"[WARN] Could not get launch agents: {e}")
        
        return agents_info
    
    def _get_system_load(self) -> Dict[str, Any]:
        """
        Get system load information.
        
        Returns:
            System load dict
        """
        try:
            output = self._execute_command(["uptime"])
            
            # Parse load averages
            load_match = re.search(r'load averages?: ([\d.]+) ([\d.]+) ([\d.]+)', output)
            
            if load_match:
                return {
                    "load_1min": float(load_match.group(1)),
                    "load_5min": float(load_match.group(2)),
                    "load_15min": float(load_match.group(3))
                }
        except Exception as e:
            print(f"[WARN] Could not get system load: {e}")
        
        return {}
    
    def _get_top_processes(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get top processes by CPU usage.
        
        Args:
            count: Number of top processes to return
        
        Returns:
            List of top processes
        """
        top_processes = []
        
        try:
            # Use top in logging mode
            output = self._execute_command(["top", "-l", "1", "-n", str(count), "-o", "cpu"])
            
            # Parse top output
            in_process_list = False
            for line in output.split('\n'):
                if "PID" in line and "COMMAND" in line:
                    in_process_list = True
                    continue
                
                if in_process_list and line.strip():
                    parts = line.split()
                    if len(parts) >= 12:
                        try:
                            top_processes.append({
                                "pid": parts[0],
                                "command": parts[1],
                                "cpu_percent": float(parts[2].rstrip('%')),
                                "memory": parts[7]
                            })
                        except (ValueError, IndexError):
                            continue
                    
                    if len(top_processes) >= count:
                        break
        except Exception as e:
            print(f"[WARN] Could not get top processes: {e}")
        
        return top_processes
    
    def _check_kernel_extensions(self) -> Dict[str, Any]:
        """
        Check loaded kernel extensions.
        
        Returns:
            Kernel extension info
        """
        try:
            output = self._execute_command(["kextstat"])
            
            # Count loaded kexts
            kext_count = len([line for line in output.split('\n') if line.strip()]) - 1  # Subtract header
            
            # Check for third-party kexts (non-Apple)
            third_party_kexts = []
            for line in output.split('\n'):
                if line.strip() and "com.apple" not in line and "Index" not in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        third_party_kexts.append({
                            "bundle_id": parts[5],
                            "version": parts[6] if len(parts) > 6 else "unknown"
                        })
            
            return {
                "total_kexts": kext_count,
                "third_party_count": len(third_party_kexts),
                "third_party_kexts": third_party_kexts[:10]  # Limit to 10
            }
        except Exception as e:
            print(f"[WARN] Could not check kernel extensions: {e}")
            return {}
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect process and service information.
        
        Returns:
            Dict containing process information
        """
        process_info = {
            "process_info": {
                "security_tools": self._get_running_security_tools(),
                "launch_agents": self._get_launch_agents(),
                "system_load": self._get_system_load(),
                "top_processes": self._get_top_processes(count=5),
                "kernel_extensions": self._check_kernel_extensions()
            }
        }
        
        return process_info

