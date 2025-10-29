#!/usr/bin/env python3
"""
Mac OS Telemetry Agent

Author: Adrian Johnson <adrian207@gmail.com>

Main agent process that coordinates telemetry collection and reporting
to the central platform.
"""

import json
import platform
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Agent configuration
AGENT_VERSION = "0.9.3"
DEFAULT_CONFIG_PATH = "/etc/zerotrust-agent/config.json"
DEFAULT_COLLECTION_INTERVAL = 300  # 5 minutes
DEFAULT_API_ENDPOINT = "http://localhost:8000"


class TelemetryAgent:
    """
    Main telemetry agent class.
    
    Coordinates collection of device telemetry and reporting to the platform.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the telemetry agent.
        
        Args:
            config_path: Path to agent configuration file
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.device_id = self._get_device_id()
        self.session = self._create_session()
        self.collectors = []
        self.running = False
        
        # Initialize collectors
        self._initialize_collectors()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from file.
        
        Returns:
            Dict containing agent configuration
        """
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"[INFO] Loaded configuration from {self.config_path}")
                return config
            except Exception as e:
                print(f"[ERROR] Failed to load config: {e}")
        
        # Return default configuration
        return {
            "api_endpoint": DEFAULT_API_ENDPOINT,
            "api_key": None,
            "collection_interval": DEFAULT_COLLECTION_INTERVAL,
            "device_name": platform.node(),
            "collectors_enabled": {
                "system_info": True,
                "security_status": True,
                "network_info": True,
                "process_info": True,
                "software_inventory": True
            },
            "log_level": "INFO"
        }
    
    def _get_device_id(self) -> str:
        """
        Get unique device identifier.
        
        Returns:
            Device ID string
        """
        # Try to get device ID from config
        device_id = self.config.get("device_id")
        
        if not device_id:
            # Generate device ID from hardware serial or UUID
            try:
                import subprocess
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                for line in result.stdout.split('\n'):
                    if "Serial Number" in line:
                        device_id = line.split(':')[1].strip()
                        break
            except Exception as e:
                print(f"[WARN] Could not get hardware serial: {e}")
                device_id = platform.node()
        
        return device_id
    
    def _create_session(self) -> requests.Session:
        """
        Create HTTP session with retry logic.
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            "User-Agent": f"ZeroTrust-Agent/{AGENT_VERSION}",
            "Content-Type": "application/json"
        })
        
        # Add API key if configured
        if self.config.get("api_key"):
            session.headers.update({
                "Authorization": f"Bearer {self.config['api_key']}"
            })
        
        return session
    
    def _initialize_collectors(self):
        """Initialize all telemetry collectors."""
        from agent.collectors import (
            SystemInfoCollector,
            SecurityStatusCollector,
            NetworkInfoCollector,
            ProcessInfoCollector,
            SoftwareInventoryCollector
        )
        
        collectors_enabled = self.config.get("collectors_enabled", {})
        
        if collectors_enabled.get("system_info", True):
            self.collectors.append(SystemInfoCollector())
        
        if collectors_enabled.get("security_status", True):
            self.collectors.append(SecurityStatusCollector())
        
        if collectors_enabled.get("network_info", True):
            self.collectors.append(NetworkInfoCollector())
        
        if collectors_enabled.get("process_info", True):
            self.collectors.append(ProcessInfoCollector())
        
        if collectors_enabled.get("software_inventory", True):
            self.collectors.append(SoftwareInventoryCollector())
        
        print(f"[INFO] Initialized {len(self.collectors)} collectors")
    
    def collect_telemetry(self) -> Dict[str, Any]:
        """
        Collect telemetry from all enabled collectors.
        
        Returns:
            Dict containing all collected telemetry
        """
        telemetry = {
            "device_id": self.device_id,
            "agent_version": AGENT_VERSION,
            "collection_time": datetime.now(UTC).isoformat(),
            "hostname": platform.node(),
            "os_type": platform.system(),
            "os_version": platform.mac_ver()[0] if platform.system() == "Darwin" else platform.release()
        }
        
        collection_errors = []
        
        for collector in self.collectors:
            try:
                collector_name = collector.__class__.__name__
                print(f"[DEBUG] Running {collector_name}...")
                
                data = collector.collect()
                telemetry.update(data)
                
            except Exception as e:
                error_msg = f"{collector.__class__.__name__}: {str(e)}"
                collection_errors.append(error_msg)
                print(f"[ERROR] {error_msg}")
        
        if collection_errors:
            telemetry["collection_errors"] = collection_errors
        
        return telemetry
    
    def send_telemetry(self, telemetry: Dict[str, Any]) -> bool:
        """
        Send telemetry data to the platform.
        
        Args:
            telemetry: Telemetry data to send
        
        Returns:
            True if successful, False otherwise
        """
        api_endpoint = self.config["api_endpoint"]
        url = f"{api_endpoint}/api/v1/telemetry"
        
        try:
            response = self.session.post(
                url,
                json=telemetry,
                timeout=30
            )
            response.raise_for_status()
            
            print(f"[INFO] Telemetry sent successfully (status: {response.status_code})")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send telemetry: {e}")
            return False
    
    def run_once(self) -> bool:
        """
        Run single collection and reporting cycle.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"[INFO] Starting telemetry collection...")
        
        try:
            # Collect telemetry
            telemetry = self.collect_telemetry()
            
            # Send to platform
            success = self.send_telemetry(telemetry)
            
            if success:
                print(f"[INFO] Collection cycle completed successfully")
            else:
                print(f"[WARN] Collection cycle completed with errors")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] Collection cycle failed: {e}")
            return False
    
    def run(self):
        """
        Run agent in continuous mode.
        
        Collects and reports telemetry at configured intervals.
        """
        self.running = True
        interval = self.config.get("collection_interval", DEFAULT_COLLECTION_INTERVAL)
        
        print(f"[INFO] Starting telemetry agent v{AGENT_VERSION}")
        print(f"[INFO] Device ID: {self.device_id}")
        print(f"[INFO] API Endpoint: {self.config['api_endpoint']}")
        print(f"[INFO] Collection interval: {interval} seconds")
        print(f"[INFO] Press Ctrl+C to stop")
        
        try:
            while self.running:
                self.run_once()
                
                # Sleep until next collection
                print(f"[INFO] Sleeping for {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down agent...")
            self.running = False
        except Exception as e:
            print(f"[ERROR] Agent crashed: {e}")
            raise
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def main():
    """Main entry point for the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mac OS Telemetry Agent")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't run as daemon)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ZeroTrust Agent v{AGENT_VERSION}"
    )
    
    args = parser.parse_args()
    
    # Check if running on Mac OS
    if platform.system() != "Darwin":
        print("[ERROR] This agent is designed for Mac OS only")
        sys.exit(1)
    
    # Create and run agent
    agent = TelemetryAgent(config_path=args.config)
    
    if args.once:
        success = agent.run_once()
        sys.exit(0 if success else 1)
    else:
        agent.run()


if __name__ == "__main__":
    main()

