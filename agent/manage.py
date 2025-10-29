#!/usr/bin/env python3
"""
ZeroTrust Agent Management CLI

Author: Adrian Johnson <adrian207@gmail.com>

Command-line tool for managing the telemetry agent.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

LAUNCH_DAEMON_LABEL = "com.zerotrust.agent"
LAUNCH_DAEMON_PLIST = "/Library/LaunchDaemons/com.zerotrust.agent.plist"
CONFIG_FILE = "/etc/zerotrust-agent/config.json"
LOG_FILE = "/var/log/zerotrust-agent/agent.log"
ERROR_LOG_FILE = "/var/log/zerotrust-agent/agent.error.log"


class AgentManager:
    """Manages the telemetry agent service."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self.is_root = (subprocess.run(["id", "-u"], capture_output=True).stdout.strip() == b"0")
    
    def _require_root(self):
        """Check if running as root."""
        if not self.is_root:
            print("[ERROR] This command requires root privileges (use sudo)")
            sys.exit(1)
    
    def _run_command(self, cmd: list) -> tuple:
        """
        Run a shell command.
        
        Args:
            cmd: Command and arguments as list
        
        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            return (result.returncode == 0, result.stdout + result.stderr)
        except Exception as e:
            return (False, str(e))
    
    def status(self):
        """Check agent status."""
        print("ZeroTrust Agent Status")
        print("=" * 50)
        
        # Check if LaunchDaemon is loaded
        success, output = self._run_command(["launchctl", "list"])
        
        if LAUNCH_DAEMON_LABEL in output:
            print(f"✓ Agent is RUNNING")
            
            # Get PID
            for line in output.split('\n'):
                if LAUNCH_DAEMON_LABEL in line:
                    parts = line.split()
                    if len(parts) >= 1 and parts[0].isdigit():
                        print(f"  PID: {parts[0]}")
                    break
        else:
            print(f"✗ Agent is NOT running")
        
        # Check configuration
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            print(f"✓ Configuration: {CONFIG_FILE}")
            
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    print(f"  API Endpoint: {config.get('api_endpoint')}")
                    print(f"  Collection Interval: {config.get('collection_interval')}s")
            except Exception as e:
                print(f"  [WARN] Could not read config: {e}")
        else:
            print(f"✗ Configuration not found: {CONFIG_FILE}")
        
        # Check LaunchDaemon plist
        plist_path = Path(LAUNCH_DAEMON_PLIST)
        if plist_path.exists():
            print(f"✓ LaunchDaemon: {LAUNCH_DAEMON_PLIST}")
        else:
            print(f"✗ LaunchDaemon not found: {LAUNCH_DAEMON_PLIST}")
        
        # Check log files
        log_path = Path(LOG_FILE)
        if log_path.exists():
            size_mb = log_path.stat().st_size / (1024 * 1024)
            print(f"✓ Log File: {LOG_FILE} ({size_mb:.2f} MB)")
        else:
            print(f"  Log File: {LOG_FILE} (not created yet)")
    
    def start(self):
        """Start the agent."""
        self._require_root()
        
        print("Starting ZeroTrust Agent...")
        
        success, output = self._run_command(["launchctl", "load", LAUNCH_DAEMON_PLIST])
        
        if success or "already loaded" in output.lower():
            print("✓ Agent started successfully!")
        else:
            print(f"✗ Failed to start agent: {output}")
            sys.exit(1)
    
    def stop(self):
        """Stop the agent."""
        self._require_root()
        
        print("Stopping ZeroTrust Agent...")
        
        success, output = self._run_command(["launchctl", "unload", LAUNCH_DAEMON_PLIST])
        
        if success or "could not find" in output.lower():
            print("✓ Agent stopped successfully!")
        else:
            print(f"✗ Failed to stop agent: {output}")
            sys.exit(1)
    
    def restart(self):
        """Restart the agent."""
        self._require_root()
        
        print("Restarting ZeroTrust Agent...")
        self.stop()
        import time
        time.sleep(2)
        self.start()
    
    def logs(self, follow: bool = False, lines: Optional[int] = None):
        """View agent logs."""
        log_path = Path(LOG_FILE)
        
        if not log_path.exists():
            print(f"[ERROR] Log file not found: {LOG_FILE}")
            sys.exit(1)
        
        if follow:
            # Follow log in real-time
            try:
                subprocess.run(["tail", "-f", LOG_FILE])
            except KeyboardInterrupt:
                print("\n[INFO] Stopped following logs")
        else:
            # Show last N lines
            cmd = ["tail"]
            if lines:
                cmd.extend(["-n", str(lines)])
            else:
                cmd.extend(["-n", "50"])
            cmd.append(LOG_FILE)
            
            subprocess.run(cmd)
    
    def errors(self, lines: Optional[int] = None):
        """View agent error logs."""
        error_log_path = Path(ERROR_LOG_FILE)
        
        if not error_log_path.exists():
            print("[INFO] No error log found - agent may not have encountered errors")
            return
        
        cmd = ["tail"]
        if lines:
            cmd.extend(["-n", str(lines)])
        else:
            cmd.extend(["-n", "50"])
        cmd.append(ERROR_LOG_FILE)
        
        subprocess.run(cmd)
    
    def test(self):
        """Run agent in test mode (single collection cycle)."""
        print("Running agent test collection...")
        
        try:
            result = subprocess.run([
                "python3",
                "/usr/local/zerotrust/agent/agent.py",
                "--config", CONFIG_FILE,
                "--once"
            ])
            
            if result.returncode == 0:
                print("\n✓ Test collection completed successfully!")
            else:
                print("\n✗ Test collection failed!")
                sys.exit(1)
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            sys.exit(1)
    
    def config_show(self):
        """Display current configuration."""
        config_path = Path(CONFIG_FILE)
        
        if not config_path.exists():
            print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
            sys.exit(1)
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            print("Current Agent Configuration:")
            print("=" * 50)
            print(json.dumps(config, indent=2))
        except Exception as e:
            print(f"[ERROR] Failed to read configuration: {e}")
            sys.exit(1)
    
    def config_set(self, key: str, value: str):
        """Update configuration value."""
        self._require_root()
        
        config_path = Path(CONFIG_FILE)
        
        if not config_path.exists():
            print(f"[ERROR] Configuration file not found: {CONFIG_FILE}")
            sys.exit(1)
        
        try:
            # Read current config
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Update value (support nested keys with dot notation)
            keys = key.split('.')
            target = config
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            
            # Try to parse value as JSON (for numbers, booleans, etc.)
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value
            
            target[keys[-1]] = parsed_value
            
            # Write updated config
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Updated {key} = {parsed_value}")
            print("[INFO] Restart the agent for changes to take effect")
        except Exception as e:
            print(f"[ERROR] Failed to update configuration: {e}")
            sys.exit(1)
    
    def uninstall(self):
        """Uninstall the agent."""
        self._require_root()
        
        print("⚠ WARNING: This will completely remove the ZeroTrust Agent")
        response = input("Are you sure? (yes/no): ")
        
        if response.lower() != "yes":
            print("Uninstall cancelled")
            return
        
        print("Uninstalling agent...")
        
        # Stop agent
        print("  Stopping agent...")
        self._run_command(["launchctl", "unload", LAUNCH_DAEMON_PLIST])
        
        # Remove files
        print("  Removing files...")
        paths_to_remove = [
            LAUNCH_DAEMON_PLIST,
            "/usr/local/zerotrust",
            "/etc/zerotrust-agent",
            "/var/log/zerotrust-agent"
        ]
        
        for path in paths_to_remove:
            self._run_command(["rm", "-rf", path])
        
        print("✓ Agent uninstalled successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ZeroTrust Agent Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Status command
    subparsers.add_parser('status', help='Show agent status')
    
    # Start/Stop/Restart commands
    subparsers.add_parser('start', help='Start the agent')
    subparsers.add_parser('stop', help='Stop the agent')
    subparsers.add_parser('restart', help='Restart the agent')
    
    # Logs commands
    logs_parser = subparsers.add_parser('logs', help='View agent logs')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow log output')
    logs_parser.add_argument('-n', '--lines', type=int, help='Number of lines to show')
    
    errors_parser = subparsers.add_parser('errors', help='View error logs')
    errors_parser.add_argument('-n', '--lines', type=int, help='Number of lines to show')
    
    # Test command
    subparsers.add_parser('test', help='Run test collection')
    
    # Config commands
    subparsers.add_parser('config-show', help='Show current configuration')
    
    config_set_parser = subparsers.add_parser('config-set', help='Update configuration value')
    config_set_parser.add_argument('key', help='Configuration key (use dot notation for nested keys)')
    config_set_parser.add_argument('value', help='New value')
    
    # Uninstall command
    subparsers.add_parser('uninstall', help='Uninstall the agent')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = AgentManager()
    
    # Execute command
    if args.command == 'status':
        manager.status()
    elif args.command == 'start':
        manager.start()
    elif args.command == 'stop':
        manager.stop()
    elif args.command == 'restart':
        manager.restart()
    elif args.command == 'logs':
        manager.logs(follow=args.follow, lines=args.lines)
    elif args.command == 'errors':
        manager.errors(lines=args.lines)
    elif args.command == 'test':
        manager.test()
    elif args.command == 'config-show':
        manager.config_show()
    elif args.command == 'config-set':
        manager.config_set(args.key, args.value)
    elif args.command == 'uninstall':
        manager.uninstall()


if __name__ == "__main__":
    main()

